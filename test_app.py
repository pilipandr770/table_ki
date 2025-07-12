import pytest
import os
import tempfile
from app import create_app, db
from app.models import User, UserRole

@pytest.fixture
def app():
    """Create application for testing."""
    db_fd, db_path = tempfile.mkstemp()
    
    config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    }
    
    app = create_app('testing')
    app.config.update(config)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def auth(client):
    """Authentication helper."""
    class AuthActions:
        def __init__(self, client):
            self._client = client
        
        def login(self, email='test@example.com', password='testpass'):
            return self._client.post('/auth/login', data={
                'email': email,
                'password': password
            })
        
        def logout(self):
            return self._client.get('/auth/logout')
    
    return AuthActions(client)

def test_app_creation(app):
    """Test app creation."""
    assert app is not None
    assert app.config['TESTING'] is True

def test_index_page(client):
    """Test index page loads."""
    response = client.get('/')
    assert response.status_code == 200

def test_user_registration(app, client):
    """Test user registration."""
    with app.app_context():
        response = client.post('/auth/register', data={
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password2': 'testpass123',
            'language_preference': 'en'
        })
        
        # Should redirect to subscription page
        assert response.status_code == 302
        
        # Check user was created
        user = User.query.filter_by(email='test@example.com').first()
        assert user is not None
        assert user.first_name == 'Test'
        assert not user.is_approved  # Should not be approved by default

def test_admin_access_denied(client):
    """Test admin access is denied for unauthenticated users."""
    response = client.get('/admin/')
    assert response.status_code == 302  # Redirect to login

def test_api_auth_required(client):
    """Test API endpoints require authentication."""
    response = client.post('/api/chat/send', json={
        'session_id': 1,
        'message': 'test'
    })
    assert response.status_code == 302  # Redirect to login

if __name__ == '__main__':
    pytest.main([__file__])

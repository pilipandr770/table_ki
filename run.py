import os
from app import create_app, db
from app.models import User, Subscription, ExcelFile, ChatSession, ChatMessage
from flask_migrate import upgrade

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Subscription': Subscription, 
            'ExcelFile': ExcelFile, 'ChatSession': ChatSession, 
            'ChatMessage': ChatMessage}

@app.cli.command()
def deploy():
    """Run deployment tasks."""
    # Create database tables
    db.create_all()
    
    # Create admin user if it doesn't exist
    admin_email = 'admin@example.com'
    admin = User.query.filter_by(email=admin_email).first()
    if not admin:
        from app.models import UserRole
        admin = User(
            email=admin_email,
            first_name='Admin',
            last_name='User',
            role=UserRole.ADMIN,
            is_approved=True,
            language_preference='en'
        )
        admin.set_password('admin123')  # Change this in production!
        db.session.add(admin)
        db.session.commit()
        print(f'Created admin user: {admin_email} / admin123')
    
    print('Deployment completed!')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

"""
Flask CLI commands for user management
"""
import click
from flask.cli import with_appcontext
from app import db
from app.models import User, UserRole

@click.command()
@click.argument('email')
@click.option('--password', default='admin123', help='Password for the admin user')
@click.option('--first-name', default='Admin', help='First name')
@click.option('--last-name', default='User', help='Last name')
@with_appcontext
def create_admin(email, password, first_name, last_name):
    """Create an admin user."""
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=email.lower()).first()
    if existing_user:
        click.echo(f"User with email {email} already exists!")
        # Make existing user admin
        existing_user.role = UserRole.ADMIN
        existing_user.is_approved = True
        db.session.commit()
        click.echo(f"✅ User {email} is now an admin!")
        return
    
    # Create new admin user
    admin_user = User(
        email=email.lower(),
        first_name=first_name,
        last_name=last_name,
        role=UserRole.ADMIN,
        is_approved=True,
        language_preference='ru'
    )
    admin_user.set_password(password)
    
    db.session.add(admin_user)
    db.session.commit()
    
    click.echo(f"✅ Admin user created successfully!")
    click.echo(f"📧 Email: {email}")
    click.echo(f"🔑 Password: {password}")
    click.echo(f"👤 Name: {first_name} {last_name}")
    click.echo(f"🔐 Role: Administrator")

def init_app(app):
    app.cli.add_command(create_admin)

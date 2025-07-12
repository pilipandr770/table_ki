# Excel Chat Assistant Setup Script
Write-Host "Starting Excel Chat Assistant Setup..." -ForegroundColor Green
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8 or higher and try again" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Set environment variables
$env:FLASK_APP = "run.py"
$env:FLASK_ENV = "development"

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "Please edit .env file with your API keys before continuing" -ForegroundColor Yellow
    Read-Host "Press Enter when you've configured your .env file"
}

# Install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Blue
try {
    pip install -r requirements.txt
    Write-Host "Dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Host "Error installing dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Initialize database
Write-Host "Setting up database..." -ForegroundColor Blue
try {
    python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('Database created successfully')"
    Write-Host "Database setup completed" -ForegroundColor Green
} catch {
    Write-Host "Error creating database" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Create admin user
Write-Host "Creating admin user..." -ForegroundColor Blue
try {
    python -c "from run import app; app.app_context().push(); from flask.cli import with_appcontext; import click; from app.models import User, UserRole; from app import db; admin = User.query.filter_by(email='admin@example.com').first(); admin = admin or User(email='admin@example.com', first_name='Admin', last_name='User', role=UserRole.ADMIN, is_approved=True, language_preference='en'); admin.set_password('admin123'); db.session.add(admin); db.session.commit(); print('Admin user created: admin@example.com / admin123')"
    Write-Host "Admin user setup completed" -ForegroundColor Green
} catch {
    Write-Host "Warning: Admin user creation had issues, but continuing..." -ForegroundColor Yellow
}

# Create directories
if (-not (Test-Path "uploads")) {
    New-Item -ItemType Directory -Path "uploads" | Out-Null
    Write-Host "Created uploads directory" -ForegroundColor Green
}

if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
    Write-Host "Created logs directory" -ForegroundColor Green
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Setup completed successfully!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Ensure .env file has your API keys configured" -ForegroundColor White
Write-Host "2. Run: python run.py" -ForegroundColor White
Write-Host "3. Visit: http://localhost:5000" -ForegroundColor White
Write-Host "4. Admin login: admin@example.com / admin123" -ForegroundColor White
Write-Host ""

$startServer = Read-Host "Would you like to start the development server now? (y/N)"
if ($startServer -eq "y" -or $startServer -eq "Y") {
    Write-Host "Starting development server..." -ForegroundColor Green
    python run.py
} else {
    Write-Host "Setup complete. Run 'python run.py' when ready to start the server." -ForegroundColor Green
}

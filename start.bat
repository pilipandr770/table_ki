@echo off
echo Starting Excel Chat Assistant Setup...
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher and try again
    pause
    exit /b 1
)

echo Python found. Continuing setup...
echo.

:: Set environment variables
set FLASK_APP=run.py
set FLASK_ENV=development

:: Check if .env exists
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo Please edit .env file with your API keys before continuing
    pause
)

:: Install dependencies
echo Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error installing dependencies
    pause
    exit /b 1
)

:: Initialize database
echo Setting up database...
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('Database created successfully')"
if errorlevel 1 (
    echo Error creating database
    pause
    exit /b 1
)

:: Create admin user
echo Creating admin user...
python -c "from run import app; app.app_context().push(); from app.cli import deploy; deploy()"
if errorlevel 1 (
    echo Error creating admin user
    pause
    exit /b 1
)

:: Create directories
if not exist uploads mkdir uploads
if not exist logs mkdir logs

echo.
echo =====================================
echo Setup completed successfully!
echo =====================================
echo.
echo Next steps:
echo 1. Edit .env file with your API keys
echo 2. Run: python run.py
echo 3. Visit: http://localhost:5000
echo 4. Admin login: admin@example.com / admin123
echo.
echo Press any key to start the development server...
pause >nul

:: Start the server
python run.py

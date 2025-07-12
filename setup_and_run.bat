@echo off
echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo Setting up environment variables...
if not exist .env (
    echo Creating .env file from .env.example...
    copy .env.example .env
)

echo Initializing database...
if not exist migrations (
    python -m flask db init
)
python -m flask db migrate -m "Initial migration"
python -m flask db upgrade

echo Starting Flask application...
python run.py

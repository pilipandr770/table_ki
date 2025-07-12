# Быстрый запуск Flask приложения

## Команда для PowerShell (одной строкой):
```powershell
python -m venv venv ; .\venv\Scripts\Activate.ps1 ; pip install -r requirements.txt ; if (-not (Test-Path .env)) { Copy-Item .env.example .env } ; if (-not (Test-Path migrations)) { python -m flask db init } ; python -m flask db migrate -m "Initial migration" ; python -m flask db upgrade ; python run.py
```

## Команда для Command Prompt (одной строкой):
```cmd
python -m venv venv && venv\Scripts\activate.bat && pip install -r requirements.txt && if not exist .env copy .env.example .env && if not exist migrations python -m flask db init && python -m flask db migrate -m "Initial migration" && python -m flask db upgrade && python run.py
```

## Пошаговые команды:

### 1. Создание виртуального окружения
```bash
python -m venv venv
```

### 2. Активация виртуального окружения
**PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**Command Prompt:**
```cmd
venv\Scripts\activate.bat
```

### 3. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения
Скопируйте `.env.example` в `.env` и настройте:
```bash
copy .env.example .env
```

### 5. Инициализация базы данных
```bash
python -m flask db init
python -m flask db migrate -m "Initial migration"
python -m flask db upgrade
```

### 6. Запуск приложения
```bash
python run.py
```

## Готовые скрипты:
- `setup_and_run.bat` - для Command Prompt
- `setup_and_run.ps1` - для PowerShell

## Тестирование:
```bash
python -m pytest test_app.py -v
```

## Доступ к приложению:
После запуска приложение будет доступно по адресу: http://localhost:5000

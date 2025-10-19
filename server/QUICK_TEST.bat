@echo off
REM Quick test script for Windows
echo ========================================
echo Django Refactor - Quick Test
echo ========================================
echo.

echo Step 1: Creating migrations...
python manage.py makemigrations
if %errorlevel% neq 0 (
    echo ERROR: Migrations failed
    pause
    exit /b 1
)
echo.

echo Step 2: Running migrations...
python manage.py migrate
if %errorlevel% neq 0 (
    echo ERROR: Migration application failed
    pause
    exit /b 1
)
echo.

echo Step 3: Running Django check...
python manage.py check
if %errorlevel% neq 0 (
    echo ERROR: Django check failed
    pause
    exit /b 1
)
echo.

echo ========================================
echo SUCCESS! Configuration is working
echo ========================================
echo.
echo Next steps:
echo 1. Run: python manage.py runserver
echo 2. In another terminal: celery -A scrimgg worker --loglevel=info --pool=solo
echo 3. Test WebSocket: cd testing ^&^& python test_websocket_connection.py
echo.
pause


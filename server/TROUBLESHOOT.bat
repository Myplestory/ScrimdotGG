@echo off
REM Troubleshooting script for refactor
echo ========================================
echo Django Refactor - Troubleshooting
echo ========================================
echo.

echo Checking Python environment...
pipenv --version
if %errorlevel% neq 0 (
    echo ERROR: pipenv not found
    echo Install with: pip install pipenv
    pause
    exit /b 1
)
echo.

echo Testing imports...
pipenv run python -c "import core; import match_system; import realtime; print('✅ Imports successful')"
if %errorlevel% neq 0 (
    echo ❌ Import error - check that apps are created correctly
    pause
    exit /b 1
)
echo.

echo Checking migrations...
pipenv run python manage.py showmigrations
echo.

echo Running Django check...
pipenv run python manage.py check
if %errorlevel% neq 0 (
    echo ❌ Django check failed
    pause
    exit /b 1
)
echo.

echo Testing WebSocket routing...
pipenv run python -c "from realtime.routing import websocket_urlpatterns; print(f'✅ WebSocket routing: {len(websocket_urlpatterns)} patterns')"
if %errorlevel% neq 0 (
    echo ❌ WebSocket routing error
    pause
    exit /b 1
)
echo.

echo ========================================
echo All checks passed!
echo ========================================
echo.
echo If WebSocket still fails, check:
echo 1. Django logs in terminal where runserver is running
echo 2. server/logs/errors.log
echo 3. Run migrations if not done: python manage.py migrate
echo.
pause


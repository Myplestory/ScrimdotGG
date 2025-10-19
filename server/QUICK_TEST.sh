#!/bin/bash
# Quick test script for Linux/Mac

echo "========================================"
echo "Django Refactor - Quick Test"
echo "========================================"
echo ""

echo "Step 1: Creating migrations..."
python manage.py makemigrations
if [ $? -ne 0 ]; then
    echo "ERROR: Migrations failed"
    exit 1
fi
echo ""

echo "Step 2: Running migrations..."
python manage.py migrate
if [ $? -ne 0 ]; then
    echo "ERROR: Migration application failed"
    exit 1
fi
echo ""

echo "Step 3: Running Django check..."
python manage.py check
if [ $? -ne 0 ]; then
    echo "ERROR: Django check failed"
    exit 1
fi
echo ""

echo "========================================"
echo "SUCCESS! Configuration is working"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Run: python manage.py runserver"
echo "2. In another terminal: celery -A scrimgg worker --loglevel=info --pool=solo"
echo "3. Test WebSocket: cd testing && python test_websocket_connection.py"
echo ""


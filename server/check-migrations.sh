#!/bin/bash
# Script to check Django migrations status on remote RDS database
# This connects directly to RDS using DATABASE_URL from AWS Secrets Manager

set -e

# Configuration
AWS_REGION="us-east-2"  # Note: secrets are in us-east-2, but ECR is in us-east-1
SECRET_NAME="scrimgg/database-url"

echo "Fetching DATABASE_URL from AWS Secrets Manager..."

# Get DATABASE_URL from Secrets Manager
DATABASE_URL=$(aws secretsmanager get-secret-value \
    --secret-id $SECRET_NAME \
    --region $AWS_REGION \
    --query SecretString \
    --output text)

if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: Could not retrieve DATABASE_URL from Secrets Manager"
    exit 1
fi

echo "✓ DATABASE_URL retrieved successfully"

# Export for Django
export DATABASE_URL
export DJANGO_SETTINGS_MODULE="scrimgg.settings_production"

# Change to server directory
cd "$(dirname "$0")"

# Check if we're in a virtual environment or need to use pipenv
if command -v pipenv &> /dev/null; then
    echo "Running migrations check using Pipenv..."
    pipenv run python manage.py showmigrations
    echo ""
    echo "To check for unapplied migrations:"
    pipenv run python manage.py showmigrations --list | grep "\[ \]"
else
    echo "Running migrations check using Python..."
    python manage.py showmigrations
    echo ""
    echo "To check for unapplied migrations:"
    python manage.py showmigrations --list | grep "\[ \]"
fi



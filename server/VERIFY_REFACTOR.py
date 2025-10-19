#!/usr/bin/env python
"""
Verification script for the Django refactor.
Tests that all apps are properly configured and importable.

Run this BEFORE running migrations to catch issues early.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from django.conf import settings
from django.core.management import call_command
import importlib


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_success(text):
    """Print success message"""
    print(f"✅ {text}")


def print_error(text):
    """Print error message"""
    print(f"❌ {text}")


def print_warning(text):
    """Print warning message"""
    print(f"⚠️  {text}")


def verify_installed_apps():
    """Verify all new apps are in INSTALLED_APPS"""
    print_header("Checking INSTALLED_APPS Configuration")
    
    required_apps = ['core', 'match_system', 'match_execution', 'realtime']
    missing = []
    
    for app in required_apps:
        if app in settings.INSTALLED_APPS:
            print_success(f"{app} is in INSTALLED_APPS")
        else:
            print_error(f"{app} is NOT in INSTALLED_APPS")
            missing.append(app)
    
    if missing:
        print_error(f"Missing apps: {', '.join(missing)}")
        print_warning("Add these to INSTALLED_APPS in settings.py")
        return False
    
    return True


def verify_imports():
    """Verify all critical imports work"""
    print_header("Checking Critical Imports")
    
    imports_to_test = [
        ('core.redis_manager', 'RedisManager'),
        ('core.websocket_utils', 'WebSocketBroadcaster'),
        ('core.exceptions', 'ScrimGGException'),
        ('match_system.models', 'Match'),
        ('match_system.models', 'MatchPlayer'),
        ('match_system.models', 'VetoAction'),
        ('match_system.managers', 'MatchManager'),
        ('match_system.managers', 'MatchConfirmationManager'),
        ('match_execution.execution_manager', 'MatchExecutionManager'),
        ('realtime.consumers', 'RealtimeConsumer'),
        ('realtime.handlers', 'LobbyHandler'),
        ('realtime.handlers', 'MatchHandler'),
        ('realtime.handlers', 'VetoHandler'),
        ('realtime.handlers', 'ExecutionHandler'),
    ]
    
    failed = []
    
    for module_name, class_name in imports_to_test:
        try:
            module = importlib.import_module(module_name)
            cls = getattr(module, class_name)
            print_success(f"Imported {module_name}.{class_name}")
        except ImportError as e:
            print_error(f"Failed to import {module_name}.{class_name}: {e}")
            failed.append(f"{module_name}.{class_name}")
        except AttributeError as e:
            print_error(f"Failed to get {class_name} from {module_name}: {e}")
            failed.append(f"{module_name}.{class_name}")
    
    if failed:
        print_error(f"Failed imports: {', '.join(failed)}")
        return False
    
    return True


def verify_routing():
    """Verify WebSocket routing is configured"""
    print_header("Checking WebSocket Routing")
    
    try:
        from realtime.routing import websocket_urlpatterns
        print_success(f"WebSocket routing configured with {len(websocket_urlpatterns)} pattern(s)")
        
        # Check ASGI configuration
        try:
            from scrimgg.asgi import application
            print_success("ASGI application configured")
        except ImportError as e:
            print_error(f"ASGI application not configured: {e}")
            return False
        
        return True
    except ImportError as e:
        print_error(f"Failed to import WebSocket routing: {e}")
        return False


def verify_celery_tasks():
    """Verify Celery tasks are importable"""
    print_header("Checking Celery Tasks")
    
    tasks_to_test = [
        ('matchmaking.tasks', 'periodic_matchmaking'),
        ('matchmaking.tasks', 'cleanup_expired_queues'),
        ('match_system.tasks', 'cleanup_expired_matches'),
        ('match_system.tasks', 'check_veto_timeouts'),
    ]
    
    failed = []
    
    for module_name, task_name in tasks_to_test:
        try:
            module = importlib.import_module(module_name)
            task = getattr(module, task_name)
            print_success(f"Found task {module_name}.{task_name}")
        except ImportError as e:
            print_error(f"Failed to import {module_name}: {e}")
            failed.append(f"{module_name}.{task_name}")
        except AttributeError as e:
            print_error(f"Failed to find task {task_name} in {module_name}: {e}")
            failed.append(f"{module_name}.{task_name}")
    
    if failed:
        print_error(f"Failed task imports: {', '.join(failed)}")
        return False
    
    return True


def verify_models():
    """Verify models are properly defined"""
    print_header("Checking Models")
    
    try:
        from match_system.models import Match, MatchPlayer, VetoAction
        
        # Check model meta
        print_success(f"Match model table: {Match._meta.db_table}")
        print_success(f"MatchPlayer model table: {MatchPlayer._meta.db_table}")
        print_success(f"VetoAction model table: {VetoAction._meta.db_table}")
        
        # Check if models have required fields
        match_fields = [f.name for f in Match._meta.get_fields()]
        if 'state' in match_fields and 'team_a_players' in match_fields:
            print_success("Match model has required fields")
        else:
            print_error("Match model missing required fields")
            return False
        
        return True
    except Exception as e:
        print_error(f"Failed to verify models: {e}")
        return False


def check_migrations():
    """Check migration status"""
    print_header("Checking Migrations")
    
    try:
        # This will show which migrations need to be run
        call_command('showmigrations', '--list')
        print_success("Migration check complete (see output above)")
        return True
    except Exception as e:
        print_error(f"Failed to check migrations: {e}")
        return False


def run_django_check():
    """Run Django's system check"""
    print_header("Running Django System Check")
    
    try:
        call_command('check')
        print_success("Django system check passed")
        return True
    except Exception as e:
        print_error(f"Django system check failed: {e}")
        return False


def main():
    """Run all verification checks"""
    print_header("Django Refactor Verification")
    print("This script verifies the refactor is configured correctly")
    
    results = {
        'INSTALLED_APPS': verify_installed_apps(),
        'Imports': verify_imports(),
        'WebSocket Routing': verify_routing(),
        'Celery Tasks': verify_celery_tasks(),
        'Models': verify_models(),
        'Migrations': check_migrations(),
        'Django Check': run_django_check(),
    }
    
    # Summary
    print_header("Verification Summary")
    
    passed = sum(results.values())
    total = len(results)
    
    for check, result in results.items():
        if result:
            print_success(f"{check}: PASSED")
        else:
            print_error(f"{check}: FAILED")
    
    print("\n" + "=" * 70)
    print(f"  Results: {passed}/{total} checks passed")
    print("=" * 70)
    
    if passed == total:
        print_success("\n✨ All checks passed! Ready for testing.")
        print("\nNext steps:")
        print("1. Run: python manage.py makemigrations")
        print("2. Run: python manage.py migrate")
        print("3. Run: python manage.py runserver")
        print("4. Test WebSocket connection")
        return 0
    else:
        print_error("\n⚠️  Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("1. Add new apps to INSTALLED_APPS in settings.py")
        print("2. Update ASGI routing to import from realtime.routing")
        print("3. Create missing manager files")
        return 1


if __name__ == '__main__':
    sys.exit(main())


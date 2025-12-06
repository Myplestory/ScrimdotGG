"""
Script to prepare production config before building the app.
Copies config.prod.json to config.json
"""
import sys
import shutil
from pathlib import Path

def get_backend_dir():
    """Get the backend directory path."""
    # Script is in client/backend/scripts/, so go up 2 levels
    script_dir = Path(__file__).parent
    return script_dir.parent

def prepare_production_config():
    """Copy production config to active config."""
    backend_dir = get_backend_dir()
    config_dir = backend_dir / "config"
    
    prod_config = config_dir / "config.prod.json"
    active_config = config_dir / "config.json"
    
    if not prod_config.exists():
        print(f"Error: {prod_config} not found!")
        print("Please create config.prod.json with your AWS Django URL")
        return False
    
    # Read prod config to check if it still has placeholder
    import json
    try:
        with open(prod_config, 'r') as f:
            prod_data = json.load(f)
            api_url = prod_data.get("django", {}).get("api_url", "")
            if "YOUR_AWS_PUBLIC_IP" in api_url:
                print("WARNING: config.prod.json still contains placeholder 'YOUR_AWS_PUBLIC_IP'")
                print("Please update config.prod.json with your actual AWS Django URL before building")
                response = input("Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    return False
    except Exception as e:
        print(f"Warning: Could not validate config.prod.json: {e}")
    
    shutil.copy(prod_config, active_config)
    print(f"✓ Copied {prod_config} to {active_config}")
    print("Production config is now active")
    return True

def prepare_development_config():
    """Copy development config to active config."""
    backend_dir = get_backend_dir()
    config_dir = backend_dir / "config"
    
    dev_config = config_dir / "config.dev.json"
    active_config = config_dir / "config.json"
    
    if not dev_config.exists():
        print(f"Error: {dev_config} not found!")
        return False
    
    shutil.copy(dev_config, active_config)
    print(f"✓ Copied {dev_config} to {active_config}")
    print("Development config is now active")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--dev":
        success = prepare_development_config()
    else:
        success = prepare_production_config()
    
    sys.exit(0 if success else 1)


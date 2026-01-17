import sys
import os

def load_env():
    """
    Loads .env file into os.environ.
    Supports Dev mode (looking in root) and PyInstaller mode (sys._MEIPASS).
    """
    env_path = None
    
    # 1. Check if running as PyInstaller Bundle
    if hasattr(sys, '_MEIPASS'):
        env_path = os.path.join(sys._MEIPASS, '.env')
    else:
        # 2. Check if running in Dev (root dir)
        # Path: src/utils/env.py -> src/utils -> src -> [Root]
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        env_path = os.path.join(base_dir, '.env')

    if not env_path or not os.path.exists(env_path):
        # Silent fail or print warning, up to you. 
        # For hackathon debug, printing is good.
        print(f"[Env] Warning: .env not found at {env_path}")
        return

    print(f"[Env] Loading keys from: {env_path}")
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith("#") or "=" not in line:
                    continue
                
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                
                # Set in environment
                os.environ[key] = value
    except Exception as e:
        print(f"[Env] Error parsing file: {e}")
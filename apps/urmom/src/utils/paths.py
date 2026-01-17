import sys
import os

def get_asset_path(filename):
    """
    Get the absolute path to a resource, works for dev and for PyInstaller
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = os.path.join(sys._MEIPASS, 'assets')
    else:
        # In Dev, assets are one level up from 'src'
        # Assuming this file is in src/utils/paths.py
        base_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets')

    return os.path.join(base_path, filename)
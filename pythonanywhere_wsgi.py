"""
PythonAnywhere WSGI Configuration for LIFEXIA
Upload this file or copy its contents into the WSGI config editor on PythonAnywhere.

Path on PythonAnywhere: /var/www/YOUR_USERNAME_pythonanywhere_com_wsgi.py
"""

import sys
import os

# Add your project directory to the sys.path
project_home = '/home/YOUR_USERNAME/lifexia'  # ← Change YOUR_USERNAME
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Load environment variables from .env
from dotenv import load_dotenv
env_path = os.path.join(project_home, '.env')
load_dotenv(env_path)

# Import your Flask app
from backend.app import app as application  # noqa

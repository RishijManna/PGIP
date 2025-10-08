import os
import sys

# -----------------------------
# Add your project directory to the sys.path
# -----------------------------
project_home = '/home/rishij/my_project'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# -----------------------------
# Load environment variables from .env (optional but useful)
# -----------------------------
from dotenv import load_dotenv
env_path = os.path.join(project_home, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

# -----------------------------
# Set the Django settings module
# -----------------------------
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_project.settings')

# -----------------------------
# Get WSGI application
# -----------------------------
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

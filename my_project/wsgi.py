import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project directory to sys.path
path = '/home/RishijManna/PGI1'
if path not in sys.path:
    sys.path.append(path)

# Load .env file
load_dotenv(Path(path) / '.env')

# Set settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'my_project.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

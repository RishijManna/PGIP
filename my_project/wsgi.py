import sys
import os

# Your project path
project_home = '/home/RishijManna/PGIP'

if project_home not in sys.path:
    sys.path.append(project_home)

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'my_project.settings'
)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
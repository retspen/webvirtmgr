import os, sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "virtmgr.settings")
sys.path.append("/var/www")

# This application object is used by the development server
# as well as any WSGI server configured to use this file.
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

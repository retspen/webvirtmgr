import logging
import os
import sys

# If you deploy virtualenv
#import site
#site.addsitedir('/var/www/webvirtmgr/venv/lib/python2.7/site-packages')

# Add this file path to sys.path in order to import settings
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '../..'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'webvirtmgr.settings'
sys.stdout = sys.stderr

sys.path.append("/var/www/webvirtmgr/")

DEBUG = False

import django.core.handlers.wsgi
from django.conf import settings
application = django.core.handlers.wsgi.WSGIHandler()


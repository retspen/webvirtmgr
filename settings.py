# Django settings for webvirtmgr project.
import os
import sys

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))

if ROOT_PATH not in sys.path:
    sys.path.append(ROOT_PATH)

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Admin', 'root@localhost'),
)
MANAGERS = ADMINS
DB_PATH = os.path.join(ROOT_PATH, 'webvirtmgr.db')
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': DB_PATH,                         # Or path to database file if using sqlite3.
        'USER': '',                              # Not used with sqlite3.
        'PASSWORD': '',                          # Not used with sqlite3.
        'HOST': '',                              # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                              # Set to empty string for default. Not used with sqlite3.
    }
}
TIME_ZONE = 'Europe/Zaporozhye'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = False
USE_L10N = True
MEDIA_ROOT = os.path.abspath(os.path.join(ROOT_PATH, '..', 'webvirtmgr/virtmgr/media'))
MEDIA_URL = 'media/'
STATIC_ROOT = os.path.abspath(os.path.join(ROOT_PATH, '..', 'webvirtmgr/virtmgr/static'))
STATIC_URL = 'static/'
ADMIN_MEDIA_PREFIX = 'static/admin/'
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)
SECRET_KEY = 'fc*a)88#3de3-a@=qrb3ip=vob00nt1jcx*=a%by^*302=6x96'
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)
ROOT_URLCONF = 'webvirtmgr.urls'
TEMPLATE_DIRS = (
    os.path.abspath(os.path.join(ROOT_PATH, '..', 'webvirtmgr/virtmgr/templates')),
)
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'webvirtmgr.virtmgr',
)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

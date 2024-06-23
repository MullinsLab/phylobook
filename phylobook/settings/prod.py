"""
Django settings for phylobook project.

Generated by 'django-admin startproject' using Django 3.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

import logging
import logging.config
from django.utils.log import DEFAULT_LOGGING


import environ
import os
from pathlib import Path

import multiprocessing

# Used when SSO login is configured
from django.urls import reverse_lazy

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(DEBUG=(int, 0))
environ.Env.read_env(os.path.join(BASE_DIR.parent, '.env'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = int(env("DEBUG", default=0))

ALLOWED_HOSTS = env('DJANGO_ALLOWED_HOSTS').split(" ")

# Application definition
INSTALLED_APPS = [
    'phylobook',
    'phylobook.projects',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'guardian',
    'phylobook.uw_saml',
    'treebeard',
    "django_extensions",
]

LOGIN_TYPE = env('LOGIN_TYPE')

# django-guardian backends
AUTHENTICATION_BACKENDS = (
    'phylobook.uw_saml.backends.VVRemoteUserBackend',
    'django.contrib.auth.backends.ModelBackend', # this is default
    'guardian.backends.ObjectPermissionBackend',
)

# django-guardian - anonymous user object permissions-are disabled.
ANONYMOUS_USER_NAME = None

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.auth.middleware.PersistentRemoteUserMiddleware',
]

ROOT_URLCONF = 'phylobook.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [str(BASE_DIR.joinpath('templates'))],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django_settings_export.settings_export',
            ],
        },
    },
]

CRISPY_TEMPLATE_PACK = 'bootstrap4'

WSGI_APPLICATION = 'phylobook.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'db', # Don't change.  db is the name of the Docker service set in docker-compose.yml
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PORT': 5432,
        #'PASSWORD': env('DB_PASSWORD'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'

#CURRENT_PATH = os.path.abspath(os.path.dirname(__file__))
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

PROJECT_PATH = env('PROJECT_PATH')

SERVER_NAME = env('SERVER_NAME')

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_USE_TLS = env('EMAIL_USE_TLS')
EMAIL_PORT = int(env('EMAIL_PORT'))
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')

SERVER_EMAIL = EMAIL_HOST_USER

LOGIN_REDIRECT_URL = "/projects"
LOGOUT_REDIRECT_URL = "/projects"

LOGIN_URL = env('LOGIN_URL')
LOGIN_SSO_TITLE = ''
LOGIN_SSO_COLLABORATOR_TITLE = ''

if LOGIN_TYPE == "dual" or LOGIN_TYPE == 'sso':
    from phylobook.settings.saml import UW_SAML as UW_SAML_CONF
    UW_SAML = UW_SAML_CONF

if LOGIN_TYPE == "dual":
    LOGIN_SSO_TITLE = env('LOGIN_SSO_TITLE')
    LOGIN_SSO_COLLABORATOR_TITLE = env('LOGIN_SSO_COLLABORATOR_TITLE')

if LOGIN_TYPE == "sso":
    LOGIN_URL = reverse_lazy('saml_login')

# Settings for the colors used to tag elements in the SVG
# Any new colors added will need to be added to /phylobook/static/css/phylobook.css
ANNOTATION_COLORS = (
    {"name": "Red", "short": "red", "value": "FF0000", "swapable": True, "has_UOLs": False},
    {"name": "Neon Blue", "short": "neonblue", "value": "537EFF", "swapable": True, "has_UOLs": False},
    {"name": "Green", "short": "green", "value": "00CB85", "swapable": True, "has_UOLs": False}, 
    {"name": "Black", "short": "black", "value": "000000", "swapable": True, "has_UOLs": False}, 
    {"name": "Orange", "short": "orange", "value": "FFA500", "swapable": True, "has_UOLs": False}, 
    {"name": "Light Blue", "short": "lightblue", "value": "00E3FF", "swapable": False, "has_UOLs": True}, 
    {"name": "Lime", "short": "lime", "value": "BFEF45", "swapable": False, "has_UOLs": True}, 
    {"name": "Gray", "short": "gray", "value": "808080", "swapable": False, "has_UOLs": True}, 
    {"name": "Apricot", "short": "apricot", "value": "FFD8B1", "swapable": False, "has_UOLs": True}, 
    {"name": "Lavender", "short": "lavender", "value": "DCBEFF", "swapable": False, "has_UOLs": True}, 
    {"name": "Pink", "short": "pink", "value": "E935A1", "swapable": False, "has_UOLs": True}, 
    {"name": "Purple", "short": "purple", "value": "800080", "swapable": False, "has_UOLs": True}, 
    {"name": "Yellow", "short": "yellow", "value": "EFE645", "swapable": False, "has_UOLs": False}, 
)

SEQUENCE_ANNOTATION_COLORS = (
    {"name": "black", "value": "black"},
    {"name": "blue", "value": "blue"},
    {"name": "orange", "value": "orange"},
    {"name": "magenta", "value": "magenta"},
    {"name": "green", "value": "green"},
    {"name": "purple", "value": "purple"},
    {"name": "red", "value": "red"},
    {"name": "grey", "value": "grey"},
    {"name": "light blue", "value": "#00E3FF"},
    {"name": "brown", "value": "brown"},
)

SETTINGS_EXPORT = [
    'LOGIN_TYPE',
    'LOGIN_SSO_TITLE',
    'LOGIN_SSO_COLLABORATOR_TITLE',
    'ANNOTATION_COLORS',
    'SEQUENCE_ANNOTATION_COLORS',
    "NOTIFICATION_UPDATE_INTERVAL",
]

# Default lineage names by color.
# if os.environ.get('LINEAGE_FILE'): 
if env('LINEAGE_FILE'):   
    LINEAGE_FILE = os.path.join("/phylobook/initial_data/", env('LINEAGE_FILE'))

# Set up Logging
LOG_DIR = os.path.join(BASE_DIR, "logs")
if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)

LOGLEVEL = 'DEBUG' if DEBUG else 'INFO'

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
       'handlers': ['console', 'requests.log'],
       'level': LOGLEVEL
    },
    'formatters': {
        'verbose': {
            'format': '{levelname} [{asctime}] {pathname}:{lineno} {message}',
            'datefmt' : '%Y-%m-%d %H:%M:%S',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'django.server': DEFAULT_LOGGING['formatters']['django.server'],
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },

        'phylobook.log': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR,'phylobook.log'),
            'maxBytes': 1024*1024*5, # 5 MB
            'backupCount': 5,
            'formatter':'verbose',
        },

        'test.log': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR,'test.log'),
            'maxBytes': 1024*1024*5, # 5 MB
            'backupCount': 5,
            'formatter':'verbose',
        },

        'requests.log': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename':  os.path.join(LOG_DIR,'requests.log'),
            'maxBytes': 1024*1024*5, # 5 MB
            'backupCount': 5,
            'formatter':'verbose',
        },

        # 'django.server': {
        #     'level':'DEBUG',
        #     'class':'logging.handlers.RotatingFileHandler',
        #     'filename':  os.path.join(LOG_DIR,'requests.log'),
        #     'maxBytes': 1024*1024*5, # 5 MB
        #     'backupCount': 5,
        #     'formatter':'verbose',
        # },

        'django.server': DEFAULT_LOGGING['handlers']['django.server'],
    },
    
    'loggers': {

        # default for all undefined Python modules
        'default': {
            'level': 'WARNING',
            'handlers': ['console', 'phylobook.log'],
            'propagate': False,
        },

        # Logging for http requests
        "django.request": {
            'level': LOGLEVEL,
            'handlers': ['console', 'requests.log'],
            'propagate': False,
        },

        # Logging for our apps
        'app': {
            'level': LOGLEVEL,
            'handlers': ['console', 'phylobook.log'],
            'propagate': False,
        },

        # Logging for tests
        'test': {
            'level': LOGLEVEL,
            'handlers': ['console', 'test.log'],
        },

        # Default runserver request logging
        'django.server': DEFAULT_LOGGING['loggers']['django.server'],

        #  Logging SQL for DEBUG Begin
        'django.db.backends': {
             'level': 'DEBUG',
             'handlers': ['console'],
         }
    
    },
})

HIGHLIGHTER_MARK_WIDTH = 3
MATCH_MARK_WIDTH = 6

TREES_PER_PAGE = 10

# Importer settings
MAX_FASTA_PROCESSORS = env("MAX_FASTA_PROCESSORS", default=multiprocessing.cpu_count())
NOTIFICATION_UPDATE_INTERVAL = env("NOTIFICATION_UPDATE_INTERVAL", default=300) * 1000
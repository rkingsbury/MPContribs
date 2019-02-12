"""
Django settings for test_site project.

Generated by 'django-admin startproject' using Django 1.8.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

from django.conf.global_settings import *

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
from django_extensions.management.commands.generate_secret_key import get_random_secret_key
SECRET_KEY = get_random_secret_key()

# SECURITY WARNING: don't run with debug turned on in production!
NODE_ENV = os.environ.get('NODE_ENV', 'production')
DEBUG = bool(NODE_ENV == 'development')

ALLOWED_HOSTS = [
    'portal.mpcontribs.org', 'contribs.materialsproject.org', 'localhost',
    'jupyterhub.materialsproject.org', '127.0.0.2'
]

AUTHENTICATION_BACKENDS = (
    #'django.contrib.auth.backends.ModelBackend',
    'webtzite.backends.CASBackend',
)

from mpcontribs.users_modules import get_user_installed_apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'django_cas_ng',
    'zappa_django_utils',
    'webtzite',
    'mpcontribs.portal',
    #'mpcontribs.rest',
    'mpcontribs.explorer',
    'webpack_loader',
    'macros',
    #'corsheaders',
] + get_user_installed_apps()

MIDDLEWARE = (
    #'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'webtzite.middleware.APIKeyMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
)

ROOT_URLCONF = 'test_site.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'test_site.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'zappa_django_utils.db.backends.s3sqlite',
        'NAME': 'db.sqlite3',
        'BUCKET': 'mpcontribs-sqlite'
    }
}
#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': os.path.join(BASE_DIR,'db.sqlite3'),
#    }
#}


LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

JPY_USER = os.environ.get('JPY_USER')
PROXY_URL_PREFIX = '/flaskproxy/{}'.format(JPY_USER) if JPY_USER else ''
STATIC_URL = PROXY_URL_PREFIX + '/static/'
STATICFILES_DIRS = (os.path.join(BASE_DIR, 'dist'),)

WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': not DEBUG,
        'BUNDLE_DIR_NAME': './',
        'STATS_FILE': os.path.join(BASE_DIR, 'webpack-stats.json'),
    }
}

if os.environ.get('DEPLOYMENT') == 'MATGEN':
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

CAS_SERVER_URL = 'http://localhost:8000/cas/' if DEBUG else 'https://materialsproject.org/cas/'
CAS_VERSION = '3'
CAS_LOGOUT_COMPLETELY = False
CAS_REDIRECT_URL = '/'
CAS_RETRY_LOGIN = True
CAS_USERNAME_ATTRIBUTE = 'username'
CAS_APPLY_ATTRIBUTES_TO_USER = True

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = ALLOWED_HOSTS
CORS_ORIGIN_WHITELIST = ALLOWED_HOSTS

MPCONTRIBS_API_HOST = '0.0.0.0' if DEBUG else 'api.mpcontribs.org'
MPCONTRIBS_API_SPEC = '{}://{}{}/apispec.json'.format(
    'http' if DEBUG else 'https', MPCONTRIBS_API_HOST, ':5000' if DEBUG else ''
)

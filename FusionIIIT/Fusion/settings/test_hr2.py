"""
Test settings for HR2 module - minimal configuration with only required apps.
Runs only HR2 migrations and tests, avoiding the full migration suite.
"""

from Fusion.settings.development import *

# Override INSTALLED_APPS to only include hr2 and its dependencies
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'rest_framework',
    'rest_framework.authtoken',
    'applications.globals',
    'applications.programme_curriculum',
    'applications.academic_information',
    'applications.department',
    'applications.establishment',
    'applications.hr2',
]

# Minimal middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
]

# Use a dummy URL configuration to avoid importing full URL setup
ROOT_URLCONF = 'Fusion.urls_empty'

# Keep the same DATABASE settings from development
# Keep SECRET_KEY and other essential settings from development

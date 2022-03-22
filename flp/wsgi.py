"""
WSGI config for flp project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flp.settings')
os.environ["DJANGO_SECRET_KEY"] = "pass"
os.environ["EMAIL_APP_KEY"] ="pass"

application = get_wsgi_application()

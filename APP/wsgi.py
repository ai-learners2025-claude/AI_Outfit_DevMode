"""
WSGI config for DjangoBlog project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import sys
os.environ["PYMATTING_NO_CACHE"] = "1"

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "APP.settings")  # ✅ 確認一致

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

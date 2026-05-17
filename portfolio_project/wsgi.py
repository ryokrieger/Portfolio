import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portfolio_project.settings")

application = get_wsgi_application()

# Vercel expects the callable to be named `app`
app = application
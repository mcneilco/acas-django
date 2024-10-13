import os
import django

def pytest_configure():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'acas.settings')
    django.setup()

from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foosshare.settings')
app = Celery('foodshare')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings
from datetime import timedelta
os.environ.setdefault('DJANGO_SETTINGS_MODULE','aurora.settings')

app = Celery('aurora')
app.conf.enable_utc = False
app.conf.update(timezone = 'Europe/London')
app.config_from_object(settings, namespace='CELERY')

#CELERY BEAT SETTINGS
app.conf.beat_schedule = {
    'write-chats-db': {
        'task':'aurora_api.tasks.batch_write_to_db',
        'schedule': timedelta(minutes=1)
    }
}


app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
    

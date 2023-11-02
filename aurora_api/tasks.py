from celery import shared_task
from .celeryfuncs import r, save_data_to_db
from django.contrib.sessions.models import Session
from .sessionsmanager import SessionManager
from django.utils import timezone
from datetime import datetime, timedelta


@shared_task(bind=True)
def test_func(self):
    return 'Done'
    

@shared_task(bind=True)
def batch_write_to_db(self):
    session_keys = r.smembers('session_keys_set')
    if len(session_keys) > 0:
        for session_key in session_keys:
            save_data_to_db(session_key)
        r.srem('session_keys_set', *list(session_keys))
    
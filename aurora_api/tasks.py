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
    try:
        # Retrieve session keys from Redis set
        session_keys_set_name = 'session_keys_set'
        while True:
            # Pop one session key from the set
            session_key = r.spop(session_keys_set_name)
            if session_key is None:
                break  # Set is empty
            try:
                # Save data to the database for each session key
                save_data_to_db(session_key)
                print(f"Processed session_key: {session_key}")
            except Exception as e:
                print(f"Error processing session_key {session_key}: {e}")
    except Exception as e:
        print(f"Error retrieving or processing session keys: {e}")


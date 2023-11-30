from .extract import ModelIngredients
from django.utils import timezone
from .models import AppCredentials, Customer
from .task_utils import PerformTask
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from cryptography.fernet import Fernet
import base64
from .task_utils import PerformTask, FreeSlotChecker, get_free_dates
import json

class SessionManager:
    def __init__(self, origin):
        self._session = SessionStore()
        self.origin = origin
        self.keys = ['file','customer_name','customer_id','intents','secret','calendar_id','booking_questions', 'mappings','closing','treatment_init','email']
        
    def create_session(self):
        self._session.create()
        seasoning = ModelIngredients(self.origin).extract_data()
        for k in self.keys:
                self._session[k] = seasoning[k]
                
        self._session['input_tag'] = None  
        self._session['booking_on'] = False
        self._session['answers'] = {}
        self._session['count'] = 0 
        self._session['callbackcount'] = 0
        self._session['messages'] = []
        self._session['summary'] = {}
        self._session['consultation_summary'] = []
        self._session['question_asked'] = None
        self._session['question_keys'] = []
        self._session['rating'] = 'like'
        self._session['probe'] = False
        self._session['feedback'] = False
        self._session['origin'] = self.origin
        self._session['get_team'] = False
        self._session['cached'] = False
        self._session.save()
        return self._session


class SessionEncrypt:
    def __init__(self, encryption_key):
        self.encryption_key = encryption_key
        self.cipher = Fernet(self.encryption_key)
    
    def encrypt_encode(self, session_key):
        encoded_key = self.cipher.encrypt(session_key.encode())
        encrypted_key = base64.urlsafe_b64encode(encoded_key).decode()
        return encrypted_key
    
    def decrypt_decode(self, encrypted_key):
        decoded_key = base64.urlsafe_b64decode(encrypted_key)
        decrypted_key = self.cipher.decrypt(decoded_key).decode()
        return decrypted_key


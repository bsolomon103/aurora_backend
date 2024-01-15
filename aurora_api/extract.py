import os
from .celeryfuncs import cache_chat_message
import boto3
import torch
import json
import random
import time
import openai 
import re
import string
from rest_framework.response import Response
import pickle
from django.conf import settings
from .models import Models, Customer, AppCredentials, Chat
from .responsemanager import download_file_from_s3, download_s3_folder
from .payload import agent_router


class ModelIngredients:
    def __init__(self, origin):
        self.origin = origin
        self.dc = {}
  
    def pull_files(self):
        customer = Customer.objects.get(origin=self.origin)
        customer_name = customer.name
        customer_id = customer.id
        calendar_id = customer.calendar_id
        mappings = customer.mappings
        closing = customer.closing
        obj = Models.objects.get(customer_name=customer.id)
        app_credentials = AppCredentials.objects.get(id=1)
        secret = app_credentials.google_secret
        FILE = obj.training_file
        email = customer.email
        intents = obj.intent
        return FILE, customer_name, customer_id, intents, secret, calendar_id, mappings, closing, email
      
    def extract_data(self):
        file, customer_name, customer_id, intents, secret, calendar_id,mappings, closing,email = self.pull_files()
        self.dc['file'] = str(file)
        self.dc['intents'] = intents
        self.dc['secret'] = str(secret)
        self.dc['calendar_id'] = calendar_id
        self.dc['mappings'] = mappings
        self.dc['customer_name'] = customer_name
        self.dc['customer_id'] = customer_id
        self.dc['closing'] = closing
        self.dc['email'] = email
        return self.dc
       
    def __set_item__(self, key, value):
        self.dc[key] = value
        
    def __get__item__(self, key):
        return self.dc['key']
    

def get_response(msg, session):
    current_messages = session['messages']
    current_messages = current_messages + f"user: {msg}\n"
    session['messages'] = current_messages
    session.save()
    return agent_router(session, msg)


def files_downloader(trainingfolder):
    folder = trainingfolder
    vectorfile = os.path.join(settings.BASE_DIR, 'media', 'training_file', os.path.basename(folder))

    # Check if the local folder exists
    if os.path.exists(vectorfile):
        return

    else:
        # The local file doesn't exist, download it from S3
        download_s3_folder(trainingfolder, 'media/training_file')
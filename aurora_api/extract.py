import os
from .celeryfuncs import cache_chat_message
#from .tasks import batch_write_to_db
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
from .prediction_model import NeuralNet
from .nltk_utils import bag_of_words, tokenize
from .task_utils import PerformTask, FreeSlotChecker, get_free_dates
from .responsemanager import get_response_dates, get_response_booking, get_response_aurora, start_assessment, get_response_callback, download_file_from_s3


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
        booking_questions = customer.booking_questions
        closing = customer.closing
        obj = Models.objects.get(customer_name=customer.id)
        app_credentials = AppCredentials.objects.get(id=1)
        secret = app_credentials.google_secret
        FILE = obj.training_file
        treatment_init = customer.treatment_init
        email = customer.email
        #print(FILE)
        intents = obj.intent
        return FILE, customer_name, customer_id, intents, secret, calendar_id, booking_questions, mappings, closing, treatment_init, email
      
      
    def extract_data(self):
        file, customer_name, customer_id, intents, secret, calendar_id, booking_questions, mappings, closing, treatment_init, email = self.pull_files()
        self.dc['file'] = str(file)
        self.dc['intents'] = intents
        self.dc['secret'] = str(secret)
        self.dc['calendar_id'] = calendar_id
        self.dc['booking_questions'] = booking_questions
        self.dc['mappings'] = mappings
        self.dc['customer_name'] = customer_name
        self.dc['customer_id'] = customer_id
        self.dc['closing'] = closing
        self.dc['treatment_init'] = treatment_init
        self.dc['email'] = email
        #print(booking_questions['booking questions'].keys())
        return self.dc
       
    def __set_item__(self, key, value):
        self.dc[key] = value
    
    def __get__item__(self, key):
        return self.dc['key']
    
def get_response(msg, model, all_words, tags, session, device):
    response =""
    
    if session['probe'] and msg.lower() == 'yes':
        response = random.choices(['Glad to be of service to you','Let me know if you have any more questions',
                                    "I'm delighted to assist you.","Feel free to reach out if you need further help.",
                                    "It's my pleasure to be of help.","Don't hesitate to ask if you require additional information.",
                                    "I'm here if you have any more inquiries."
                                    ])[0]
                                    
        #Store the chat message in Redis
        cache_chat_message(session['session_key'], msg, response,session['rating'],session['intent'])
        session.save()
        return response
    elif (session['probe'] and msg.lower() == 'no') or session['callback']:
        response = get_response_callback(msg, session)
        #cache_chat_message(session['session_key'], msg, response)
        return response
        
    elif (not session['probe'] and msg.lower() == 'yes'):
        start_assessment(msg, session)
    if (session['booking_on']):
        response = get_response_booking(msg, session)
        #cache_chat_message(session['session_key'], msg, session['rating'],response)
    else:
        output = get_response_aurora(msg,model, all_words, tags, session, device)
        response = output['response']
        #cache_chat_message(session['session_key'], msg, response)
    if type(response) is list:
        placeholder = 'list of dates'
        cache_chat_message(session['session_key'],msg, session['rating'], placeholder, session['intent'])
    session.save() 
    return response
    
    
def model_builder(trainingfile):
    dc = {}

    # Specify the local file path where you expect the training file to be
    local_trainingfile = os.path.join(settings.BASE_DIR, 'media', 'training_file', os.path.basename(trainingfile))

    # Check if the local file exists
    if os.path.exists(local_trainingfile):
        data = torch.load(local_trainingfile, map_location=torch.device('cpu'))
        model = NeuralNet(data['input_size'], data['hidden_size'], data['output_size']).to(torch.device('cpu'))
        model.load_state_dict(data['model_state'])
        model.eval()
        dc['tags'] = data['tags']
        dc['all_words'] = data['all_words']
        dc['model'] = model
    else:
        # The local file doesn't exist, download it from S3
        local_trainingfile = download_file_from_s3('training_file', trainingfile)
        if local_trainingfile:
            data = torch.load(local_trainingfile, map_location=torch.device('cpu'))
            model = NeuralNet(data['input_size'], data['hidden_size'], data['output_size']).to(torch.device('cpu'))
            model.load_state_dict(data['model_state'])
            model.eval()
            dc['tags'] = data['tags']
            dc['all_words'] = data['all_words']
            dc['model'] = model

    return dc
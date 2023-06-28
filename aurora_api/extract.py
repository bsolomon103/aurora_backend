import os
from .models import Models, Customer, AppCredentials
import torch
import json
from .prediction_model import NeuralNet
from .nltk_utils import bag_of_words, tokenize
import random
import time
import openai 
openai.api_key = "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"
from .openaiworkers import worker_one, worker_two
import re
import string
from rest_framework.response import Response
import pickle
from .task_utils import PerformTask, FreeSlotChecker
from .responsemanager import get_response_dates, get_response_booking, get_response_aurora

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
        obj = Models.objects.get(customer_name=customer.id)
        app_credentials = AppCredentials.objects.get(id=1)
        secret = app_credentials.google_secret
        FILE = obj.training_file
        intents = obj.intent
        
        return FILE, customer_name, customer_id, intents, secret, calendar_id, booking_questions, mappings
      
      
    def extract_data(self):
        file, customer_name, customer_id, intents, secret, calendar_id, booking_questions, mappings = self.pull_files()
        self.dc['file'] = str(file)
        self.dc['intents'] = intents
        self.dc['secret'] = str(secret)
        self.dc['calendar_id'] = calendar_id
        self.dc['booking_questions'] = booking_questions
        self.dc['mappings'] = mappings
        self.dc['customer_name'] = customer_name
        self.dc['customer_id'] = customer_id
        #print(booking_questions['booking questions'].keys())
        return self.dc
       
    def __set_item__(self, key, value):
        self.dc[key] = value
    
    def __get__item__(self, key):
        return self.dc['key']
        

def _get_response(msg, model, all_words, tags, intents, device):
    sentence = tokenize(msg)
    X = bag_of_words(sentence, all_words)
    X = X.reshape(1, X.shape[0])
    X = torch.from_numpy(X).to(device)
    output = model(X)
    _,predicted = torch.max(output,dim=1)
    tag = tags[predicted.item()]
    probs = torch.softmax(output,dim=1)
    prob = probs[0][predicted.item()]
    dc = {}
    dc['input_tag'] = tag
    # Client model call - first response to check if and only if a questions can't be matched will it proceed
    #print(prob.item(), tag)
    if prob.item() >= 0.99:
        for intent in intents['intents']: 
            if tag == intent['tag']:
                dc['response'] =  random.choices(intent['responses'])[0]
    else:
        response = worker_one(msg)
        dc['response'] = response
    return dc

  
def get_response(msg, model, all_words, tags, session, device):
    if msg.lower() == 'book me':
        response = get_response_dates(msg, session)
    elif session['booking_on'] == True:
        response = get_response_booking(msg, session)
    else:
        output = get_response_aurora(msg, model, all_words, tags, session, device)
        response = output['response']
    return response
    
    

def model_builder(trainingfile):
    dc = {}
    data = torch.load(trainingfile, map_location=torch.device('cpu'))
    model = NeuralNet(data['input_size'], data['hidden_size'], data['output_size']).to(torch.device('cpu'))
    model.load_state_dict(data['model_state'])
    model.eval()
    dc['tags'] = data['tags']
    dc['all_words'] = data['all_words']
    dc['model'] = model
    return dc
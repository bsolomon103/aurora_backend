import os
from .models import Models
import torch
import json
from .prediction_model import NeuralNet
from .nltk_utils import bag_of_words, tokenize
import random
import time
import openai 
openai.api_key = "*"
import re
import string
from .modelencoder import processes
from rest_framework.response import Response
import pickle

append_end = f"Type <img src='https://img.icons8.com/?size=512&id=1XyoV2ktiJK2&format=png'style='height: 20px; width: 25px;' alt='yes'></img> below to explore your options with one of our experts immediately."


class ModelIngredients:
    def __init__(self, origin):
        self.origin = origin
        self.dc = {}
  
    def pull_files(self):
        obj = Models.objects.get(origin = self.origin)
        FILE = obj.training_file
        intents = obj.intent
        token = obj.tokens
        smart_funnel = obj.smart_funnel
        return FILE, intents, token,smart_funnel
      
    def extract_data(self):
        file, intents,token, smart_funnel = self.pull_files()
        self.dc['file'] = str(file)
        self.dc['intents'] = intents
        self.dc['token'] = str(token)
        self.dc['smart_funnel'] = smart_funnel
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
    print(tag, prob.item())
    # Client model call - first response to check if and only if a questions can't be matched will it proceed
    if prob.item() > 0.99:
        for intent in intents['intents']: 
            if tag == intent['tag']:
                '''
                if tag.endswith('assess') or tag.endswith('booking'):
                    dc['process'] = tag
                '''
                dc['response'] =  random.choices(intent['responses'])[0]
                return dc
    else:
        'consider moving these to a seperate file build an API class and just change the system content using a dictionary'    
        # Worker 1: 1st API call to check for a tag match
        response = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo",

            messages = [{'role': 'system', 'content': f"You are a helpful assistant that works for a dentist practise in the uk. You always provide responses limited to 25 words max. All responses that reference 'the dentist' should be changed to 'us' or 'we' as the dentist able to provide the services suggested."},
                        {'role': 'user', 'content': msg}])
      

        response = response['choices'][0]['message']['content'].lower()
        
      
        response = f"{response.capitalize()}<br/><br/>{append_end}"
        dc['response'] = response
        return dc
        
    

def get_response(msg, smart_funnel, model, all_words, tags, intents, device):
    output = _get_response(msg, model, all_words, tags, intents, device)
    #print(output)
    return output
    
    

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

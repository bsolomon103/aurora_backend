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



class ModelIngredients:
    def __init__(self, customer_name):
        self.customer = customer_name
        self.dc = {}
  
    def pull_files(self):
        obj = Models.objects.get(customer_name=self.customer)
        FILE = obj.training_file
        intents = obj.intent
        token = obj.tokens
        return FILE, intents, token
      
    def extract_data(self):
        file, intents,token = self.pull_files()
        self.dc['file'] = file
        self.dc['intents'] = intents
        self.dc['token'] = str(token)
        return self.dc
       
    def __set_item__(self, key, value):
        self.dc[key] = value
    
    def __get__item__(self, key):
        return self.dc['key']

def get_response(msg, model, all_words, tags, intents, device):
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
    dc['process'] = None
  
    # Client model call - first response to check if and only if a questions can't be matched will it proceed
    if prob.item() > 0.75:
        for intent in intents['intents']: 
            if tag == intent['tag']:
                if tag.endswith('process'):
                    dc['process'] = tag
                dc['response'] =  random.choices(intent['responses'])[0]
                return dc      
    else:
        try:
            'consider moving these to a seperate file build an API class and just change the system content using a dictionary'    
            # Worker 1: 1st API call to check for a tag match
            match = openai.ChatCompletion.create(
                model = "gpt-3.5-turbo",
                messages = [{'role': 'system', 'content': f"You are a helpful assistant that categorises questions into these categories {tags}. You always respond in the format 'tag: response' Where response is the category you think the questions should be in. If not match is found respond with the phrase 'no match'"},
                            {'role': 'user', 'content': msg}])
            match = match['choices'][0]['message']['content'].lower()
            print(match)
        
            # Worker 2: 2nd API call to create a new tag
            if match == 'no match':
                newtag = openai.ChatCompletion.create(
                    model = "gpt-3.5-turbo",
                    messages = [{'role': 'system', 'content': f"You are a helpful assistant that comes up with one word categories for questions. You always respond in the format 'tag: response' Where response is the category you think the questions should be in."},
                                {'role': 'user', 'content': msg}])
                newtag = newtag['choices'][0]['message']['content'].lower()
                print(newtag)

                # Worker 3: 3rd API call to create a response
                response = 'Im sorry'
                response = openai.ChatCompletion.create(
                    model = "gpt-3.5-turbo",
                    messages = [{'role': 'system', 'content': f"You are a helpful assistant that responds to questions. If you can answer the question do so, or else say 'Im sorry I dont have the answer.'"},
                                {'role': 'user', 'content': msg}])
                
                if type(response) != str:
                    dc['response'] = response['choices'][0]['message']['content'].lower()
                    
                return dc
            #add the logic for handling where the msg can be rolles back into top layer model
            # if match, split, make trans ans loop again. 
             
        except:
            return 'Im sorry. I dont have the answer now. Try again later, Im constantly learning and might be able to answer your question later.'


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

def tmp_func(sessionobj):
    print(sessionobj['intents'])
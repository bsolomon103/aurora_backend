import os
from .models import Models
import torch
import json
from .prediction_model import NeuralNet
from .nltk_utils import bag_of_words, tokenize
import random
import time
import openai 
openai.api_key = None
import re
import string


class ModelIngredients:
    def __init__(self, customer_name):
        self.customer = customer_name
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.dc = {}

    
    def pull_file_intents(self):
        obj = Models.objects.get(customer_name=self.customer)
        FILE = obj.training_file
        intents = obj.intent
        return FILE, intents
    
    def extract_data(self):
        file, intents = self.pull_file_intents()
        data = torch.load(file)
        input_size = data['input_size']
        hidden_size = data['hidden_size']
        output_size = data['output_size']
        all_words = data["all_words"]
        tags = data['tags']
        model_state = data['model_state']
        return input_size, hidden_size, output_size, all_words, tags, model_state, intents
    
    
    def __set_item__(self, key, value):
        self.dc[key] = value
    
    def __get__item__(self, key):
        return self.dc['key']

    
    def build(self):
        try:
            i,h,o,a,t,m,intents = self.extract_data()
            model = NeuralNet(i,h,o).to(self.device)
            model.load_state_dict(m)
            model.eval()
            self.dc['all_words'] = a
            self.dc['tags'] = t
            self.dc['intents'] = intents
            self.dc['model'] = model
            self.dc['device'] = self.device
            return self.dc
        except Exception as e:
            print(e)

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
    processes = ['child registration appointment']
    # Client model call - first response to check if and only if a questions can't be matched will it proceed
    if prob.item() > 0.97:
        for intent in intents['intents']:
            if tag == intent['tag']:
                if tag in processes:
                    dc['process'] = tag
                dc['response'] = random.choice(intent["responses"])
                return dc
            'build form object here with validation will most likely need cache'
            
    else:
        try:
            'consider moving these to a seperate file build an API class and just change the system content using a dictionary'    
            # Worker 1: 1st API call to check for a tag match
            match = openai.ChatCompletion.create(
                model = "gpt-3.5-turbo",
                messages = [{'role': 'system', 'content': f"You are a helpful assistant that categorises questions into these categories {tags}. You always respond in the format 'tag: response' Where response is the category you think the questions should be in. If not match is found respond with the phrase 'no match'"},
                            {'role': 'user', 'content': msg}])
            match = match['choices'][0]['message']['content'].lower()
        
            # Worker 2: 2nd API call to create a new tag
            if match.__contains__('no match'):
                newtag = openai.ChatCompletion.create(
                    model = "gpt-3.5-turbo",
                    messages = [{'role': 'system', 'content': f"You are a helpful assistant that comes up with one word categories for questions. You always respond in the format 'tag: response' Where response is the category you think the questions should be in."},
                                {'role': 'user', 'content': msg}])
                newtag = newtag['choices'][0]['message']['content'].lower()

                # Worker 3: 3rd API call to create a response
                response = 'Im sorry'
                response = openai.ChatCompletion.create(
                    model = "gpt-3.5-turbo",
                    messages = [{'role': 'system', 'content': f"You are a helpful assistant that responds to questions. If you can answer the question do so, or else say 'Im sorry I dont have the answer.'"},
                                {'role': 'user', 'content': msg}])
                
                if type(response) != str:
                    response = response['choices'][0]['message']['content'].lower()
                return response 
            else:
                match = match.split(':')[1]
                match = match.translate(match.maketrans(' ',' ', string.punctuation)).strip()
            
                for intent in intents['intents']:
                    if intent['tag'] == match:
                        return random.choice(intent['responses'])  
        except:
            return 'Im sorry. I dont have the answer now. Try again later, Im constantly learning and might be able to answer your query later.'
          
        
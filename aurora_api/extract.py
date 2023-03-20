import os


from .models import Models
import torch
import json
from .prediction_model import NeuralNet
from .nltk_utils import bag_of_words, tokenize
import random


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

    if prob.item() > 0.75:
        for intent in intents['intents']:
            if tag == intent['tag']:
                return random.choice(intent["responses"])
            
    else:
        return 'Please be more specific with your question...'


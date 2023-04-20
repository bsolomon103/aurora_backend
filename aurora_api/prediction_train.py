import numpy as np
import random 
import json 
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from .prediction_model import NeuralNet
from .nltk_utils import bag_of_words, tokenize, stemming
import json
import time
from collections import OrderedDict
import os
from django.conf import settings

class ChatDataset(Dataset):
    def __init__(self, xtrain, ytrain):
        self.n_samples = len(xtrain)
        self.x_data = xtrain
        self.y_data = ytrain
    
    # support indexing such that dataset[i] can be used to get i-th sample
    def __getitem__(self, index):
        return self.x_data[index], self.y_data[index]
    
    def __len__(self):
        return self.n_samples

class ModelTrainingObject:
    def __init__(self, customer_name, jsonfile, hiddensize, epochs, batchsize, learningrate):
        self.customer_name = customer_name,
        self.intents = json.loads(jsonfile.decode('utf-8'))
        self.all_words = []
        self.tags = []
        self.xy = []
        self.hidden_size = int(hiddensize)
        self.epochs = int(epochs)
        self.batchsize = int(batchsize)
        self.learningrate = float(learningrate)
        print(type(self.intents))
        
    
        # loop through each sentence in our intents pattern
        for intent in self.intents['intents']:
            tag = intent['tag']
            # add tag to list
            self.tags.append(tag)
            for pattern in intent['patterns']:
                # tokenize each word in the sentence
                w = tokenize(pattern)
                # add to our words list
                self.all_words.extend(w)
                # add to xy pair
                self.xy.append((w, tag))
        
        # stem and lower each word
        ignore_words = ['?', '.', '!']
        self.all_words = [stemming(w) for w in self.all_words if w not in ignore_words]
        # remove duplicates and sort
        self.all_words = sorted(set(self.all_words))
        self.tags = sorted(set(self.tags))

    def train(self):
        x_train = []
        y_train = []
        for (pattern_sequence, tag) in self.xy:
            # X: bag of words for each pattern_sequence
            bag = bag_of_words(pattern_sequence, self.all_words)
            x_train.append(bag)
            # Y: Pytorch CrossEntropyLoss needs only class labels, not one-hot
            label = self.tags.index(tag)
            y_train.append(label)
        
        x_train = np.array(x_train)
        y_train = np.array(y_train)

        # Hyper-parameters
        input_size = len(x_train[0])
        datasetsize = len(x_train)
        output_size = len(self.tags)
        print(self.batchsize, self.hidden_size, self.epochs, self.learningrate, input_size, datasetsize)
    
        dataset = ChatDataset(x_train,y_train)
       
        train_loader = DataLoader(dataset=dataset,
                                  batch_size=self.batchsize,
                                  shuffle=True,
                                  num_workers=0
                                  )
        if torch.cuda.is_available():
            device = torch.device('cuda')
        else:
            print('No GPUs available')

        model = NeuralNet(input_size, self.hidden_size,output_size).to(device)

        # Loss and optimizer
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=self.learningrate)

        # train the model
        for epoch in range(self.epochs):
            for(words,labels) in train_loader:
                words = words.to(device)
                labels = labels.to(dtype=torch.long).to(device)

                # Forwards pass
                outputs = model(words).to(device)
                loss = criterion(outputs, labels)

                # Backwards and optimize
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            
            if (epoch+1) % 100 == 0:
                print(f"Epoch [{epoch+1}/{self.epochs}], Loss: {loss.item():.4f}")
        print(f"Final Loss: {loss.item():.4f}")
        
        data = {
            "model_state": model.state_dict(),
            "input_size": input_size,
            "hidden_size": self.hidden_size,
            "output_size": output_size,
            "all_words": self.all_words,
            "tags": self.tags
        }

        timevar = time.time()
        file_name = f"master_model_cache.pth"
        directory = os.path.join(settings.BASE_DIR, "files")
        FILE =  f"{directory}/{file_name}"
        torch.save(data, FILE)
        return self.intents, FILE




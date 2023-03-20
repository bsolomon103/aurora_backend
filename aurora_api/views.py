from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from .forms import ModelTrainingForm
from django.views import View
from .prediction_train import ModelTrainingObject
from .prediction_model import NeuralNet
from .models import Models, Customer
import random
import torch
from .extract import ModelIngredients, get_response
from .nltk_utils import tokenize, bag_of_words
from .serializers import MsgSerializer
from django.urls import reverse_lazy
import os
from django.conf import settings

# Create your views here.
class TestAPIView(GenericAPIView):
    def get(self, request):
        return Response({"message: Start building here"})
    

class ModelTrainingView(View):
    template = 'components/training.html'
    success_url = 'reverse_lazy:fill_in_here'
    def get(self, request, *args, **kwargs):
        form = ModelTrainingForm()
        ctx = {'form': form}
        return render(request, self.template, context=ctx)
    
    def post(self, request, *args, **kwargs):
        form = ModelTrainingForm(request.POST, request.FILES)
        file = None
        ctx = {'form': form, 'file': file}
        
        if form.is_valid():
            intent = request.FILES['intent'].read()
            customer_name = form.cleaned_data['customer_name']
            epochs = form.cleaned_data['epochs']
            batch_size = form.cleaned_data['batch_size']
            learning_rate = form.cleaned_data['learning_rate']
            hidden_size = form.cleaned_data['hidden_size']

            try:
                customer_obj= Customer.objects.get(name__icontains=customer_name)
                intents_json, FILE = ModelTrainingObject(customer_name, intent, hidden_size, epochs, batch_size, learning_rate).train()
                ctx = {'form':form, 'file': FILE}
                model_key = str.lower(''.join(random.choice('0123456789ABCDEF') for i in range(32)))
                queryset = Models.objects.filter(model_key = model_key)

                while len(queryset) > 0:
                    model_key = str.lower(''.join(random.choice('0123456789ABCDEF') for i in range(32)))
                    queryset = Models.objects.filter(model_key = model_key)
            
                Models.objects.create(customer_name = customer_obj,
                                        intent = intents_json,
                                        training_file = FILE,
                                        model_key = model_key
                                    )
                print('Model created successfully !')
               
                return render(request, self.template, context=ctx)
            except Exception as e:
                print(e)
                return render(request, self.template, context=ctx)

        else:
            print('Invalid Form')
            return render(request, self.template, context=ctx)
     
class ModelResponseAPI(GenericAPIView):
    '''Main API which user requests will hit and returns a response to their questions'''
    serializer_class = MsgSerializer


    def post(self, request, *args, **kwargs):   
        # Map all requests from host to relevant model
        # Add host_name to model class and add it as paramerter into Extractor

        _ingredients = ModelIngredients(1).build()  
        model = _ingredients['model']
        device = _ingredients['device']
        intents = _ingredients['intents']

        '''
        directory = os.path.join(settings.BASE_DIR, 'files')
        FILE = os.listdir(directory)

        intents = ModelIngredients(1).pull_file_intents()
        device = torch.device('cuda')
        _ingredients = torch.load(FILE[0])
        '''
        all_words = _ingredients['all_words']
        intents = _ingredients['intents']
        tags = _ingredients['tags']
        input_size = _ingredients['input_size']
        hidden_size = _ingredients['hidden_size']
        model_state = _ingredients['model_state']
        output_size = _ingredients['output_size']

        model = NeuralNet(input_size, hidden_size, output_size).to(device)
        model.load_state_dict(model_state)
        model.eval()

    
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            msg = serializer.data['msg']
            try:
                
                response = get_response(msg, model, all_words, tags, intents, device)
            

                status_code = 200
                return Response(response, status=status_code)
            except Exception as e:
                print(e)
        else:
            response = None
            status_code = 500
            return Response(response, status = status_code)
    
        


from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from .forms import ModelTrainingForm
from django.views import View
from .prediction_train import ModelTrainingObject
from .prediction_model import NeuralNet
from .models import Models, Customer
import random, string 
import torch
from .extract import ModelIngredients, get_response
from .nltk_utils import tokenize, bag_of_words
from .serializers import MsgSerializer, GetClientSerializer
from django.urls import reverse_lazy
import os
from django.conf import settings
from aurora_api.frmdskext import get_ingredients_
from rest_framework.views import APIView
from asgiref.sync import sync_to_async
import time
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect, csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework import permissions



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
                cust_id = customer_obj.id
                intents_json, FILE = ModelTrainingObject(customer_name, intent, hidden_size, epochs, batch_size, learning_rate).train()
                ctx = {'form':form, 'file': FILE}
                model_key = str.lower(''.join(random.choice('0123456789ABCDEF') for i in range(32)))
                existing_models = Models.objects.filter(customer_name = cust_id)
                if len(existing_models) > 0:
                    for i in range(len(existing_models)):
                        existing_model = existing_models[i]
                        existing_model.delete()

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
     
class ModelResponseAPI(APIView):
    '''Main API which user requests will hit and returns a response to their questions'''
    
    serializer_class = MsgSerializer
    def post(self, request, *args, **kwargs): 
        # Map all requests from host to relevant model
        # Add host_name to model class and add it as paramerter into Extractor
      
        if request.session.get('session_key') is None:
            request.session.create()
            print(request.session.session_key)
        _ingredients = ModelIngredients(1).build()  
        #_ingredients = get_ingredients_('x')
        model = _ingredients['model']
        device = _ingredients['device']
        intents = _ingredients['intents']
        all_words = _ingredients['all_words']
        tags = _ingredients['tags']
            
        
        serializer = self.serializer_class(data=request.data)
            
        if serializer.is_valid():
            msg = serializer.data['msg']
            # route process requests here if msg - yes
            # clear process here if aborted or finished
            # Only ever 1 process at a time per request.
            try: 
                output = get_response(msg, model, all_words, tags, intents, device)
                if output['process'] is None:
                    response = output['response']
                else:
                    response = output['response']
                    process = output['process']
                     
                status_code = 200
                  
                response = Response(response, status=status_code)
                response.set_cookie('my_cookie','my_value')
              
                return response
            
            except Exception as e:
                    print(e)
                    print('Error')
        else:
            response = 'Error Bro'
            status_code = 500
       

        return Response(response, status = status_code)


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(ensure_csrf_cookie, name='dispatch')
class GetCSRFTokenView(GenericAPIView):
    permission_classes = (permissions.AllowAny, )
    def get(self, request, format=None):
        return Response({'success':'CSRF Cookie set'})
'''
class GetCSRFTokenView(GenericAPIView):  
    permission_classes = (permissions.AllowAny, )
    serializer_class = GetClientSerializer
    def post(self, request, format=None):
        session = request.session.get('session_key')
        print(session)



        return Response({'success':'CSRF Cookie set'})
'''


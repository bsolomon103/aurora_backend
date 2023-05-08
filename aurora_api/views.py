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
from .extract import ModelIngredients, get_response, model_builder, tmp_func
from .nltk_utils import tokenize, bag_of_words
from .serializers import MsgSerializer, GetClientSerializer
from django.urls import reverse_lazy
import os
from django.conf import settings
from .task_utils import PerformTask
from rest_framework.views import APIView
from asgiref.sync import sync_to_async
import time
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect, csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework import permissions
import json 
import datefinder
import pickle




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
                        existing_model.intent = intents_json
                        existing_model.training_file = FILE
                        existing_model.model_key = model_key
                        print('Model updated successfully !')
                        #existing_model.delete()
                else:
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
    keys = ['file','intents','token']
    serializer_class = MsgSerializer

    def post(self, request, *args, **kwargs): 
        # Map all requests from host to relevant model
        # Add host_name to model class and add it as paramerter into Extractor   
        print(request.META['HTTP_ORIGIN'])  
        serializer = self.serializer_class(data=request.data) 
        if serializer.is_valid():
            msg  = serializer.data['msg']

        if request.session.session_key is None: 
            print('Session(no)')
            request.session.create()
            print(f'New Session Created: {request.session.session_key}')
            seasoning = ModelIngredients(1).extract_data()

            # load 'file' and 'intent' into session
            for k in self.keys:
                request.session[k] = seasoning[k]
            request.session['process'] = None  
            request.session['questionasked'] = None 
            request.session['answers'] = {}
            request.session['count'] = 0  

        else:
            print('Session(yes)')
            print(request.session.session_key)
            #tmp_func(request.session)
            #check for an active process here
            if (request.session['process'] != None and msg.lower() == 'quit'):
                request.session['process'] = None
                return Response('Process Terminated', status=200)

            elif (request.session['questionasked'] == None and request.session['process'] != None and msg.lower() == 'yes'):
                #start process
                process = request.session['process']
                intents = request.session['intents']
                for i in intents['intents']:
                    if i['tag'] == process + ' questions':
                        questions = i['patterns']
                    if i['tag'] == 'calender':
                        request.session['calendar_provider'], request.session['calendar_id'] = i['responses'][0].split(':')[0].strip(), i['responses'][0].split(':')[1].strip()
                request.session['questions'] = questions
                count = request.session['count']
                questionasked, task = request.session['questions'][count].split(':')[0], request.session['questions'][count].split(':')[1]
                request.session['questionasked'] = questionasked
                request.session['task'] = task
                request.session['answers'][questionasked] = ''
                request.session['count'] += 1
                return Response(questionasked, status=200)

            elif (request.session['questionasked'] == None and request.session['process']  != None and msg.lower() == 'no'):
                #kill process
                request.session['process'] = None
                request.session['count'] = 0
                del request.session['intents']
                return Response('Process Terminated', status=200)
            
            elif (request.session['questionasked'] != None and request.session['process'] != None):
                #continue the process
                count = request.session['count']
                if count < len(request.session['questions']):
                    questionasked = request.session['questionasked']             
                    output = PerformTask(msg, 
                                      request.session['task'], 
                                      request.session['token'],
                                      request.session['calendar_provider'],
                                      request.session['calendar_id']).do_task()
                    if output != None:
                        request.session['event_times'] = output
                    request.session['answers'][questionasked] = msg
                    questionasked, task = request.session['questions'][count].split(':')[0], request.session['questions'][count].split(':')[1]
                    request.session['questionasked'], request.session['task'] = questionasked, task
                    request.session['count'] += 1
                    return Response(questionasked, status=200)
                
                else:
                    questionasked = request.session['questionasked']
                    request.session['answers'][questionasked] = msg
                    if request.session['event_times']:
                        event = PerformTask(msg, 
                                      request.session['task'], 
                                      request.session['token'],
                                      request.session['calendar_provider'],
                                      request.session['calendar_id']).create_event(request.session['event_times']['start'],
                                                                                   request.session['event_times']['end'],
                                                                                   request.session['process'],
                                                                                   description=request.session['answers'])                 
                    request.session['questionasked'] = None
                    request.session['process'] = None
                    request.session['count'] = 0
                    return Response(event, status=200)
        payload = model_builder(os.path.join(settings.MEDIA_ROOT, request.session['file']))  
        try: 
            response = get_response(msg,
                                    payload['model'], 
                                    payload['all_words'], 
                                    payload['tags'],
                                    request.session['intents'],
                                    torch.device('cpu')
                                    )
            status_code = 200 
            if response['process'] is None:
                return Response(response['response'], status=status_code)
            else:
                request.session['process'] = response['process']
                return Response(response['response'], status=status_code)           
        except:
            pass
        response = 'Im sorry. I dont have the answer now. Try again later, Im constantly learning and might be able to answer your question later.'
        return Response(response, status=200)
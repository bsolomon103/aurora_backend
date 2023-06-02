from django.shortcuts import render
from django.http import HttpResponse
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
from .extract import ModelIngredients, get_response, model_builder
from .sessionsmanager import SessionManager
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
from django.middleware.csrf import get_token




# Create your views here.
class TestAPIView(GenericAPIView):
    def get(self, request):
        if "counter" in request.session and "counter" == 5:
            request.session["counter"] += 1
            return 
        else:
            request.session["counter"] = 1
        return HttpResponse(f"Counter: {request.session['counter']}")
    


        #return Response({"message: Start building here"})
    

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
    
 
    serializer_class = MsgSerializer
    
 
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, *kwargs)

    def post(self, request, *args, **kwargs): 
        #origin = request.META['HTTP_ORIGIN']
        origin = 'https://eac946ea7313489f9f0055b8035f47bb.vfs.cloud9.eu-west-2.amazonaws.com/'
        #origin = 'https://cd640da2747e45bdb08d9f115ec0fcda.vfs.cloud9.eu-west-2.amazonaws.com'
        serializer = self.serializer_class(data=request.data) 
        
        #print(request.META['HTTP_X_SESSION_ID'])
        
        if serializer.is_valid():
            msg  = serializer.data['msg']
       
        if request.session.session_key is None:
            request.session = SessionManager(request.session, origin, msg).create_session()
            print('[*] A session has been created [*]')
        else:
            print('Session already exists !')
            if (msg.lower() == 'quit'):
                request.session = SessionManager(request.session, origin, msg).terminate_process()
                return Response('Process Terminated', status=200)
    
            elif (request.session['input_tag'].endswith('nnex') and msg.lower() == 'yes'):
                #start assessment
                request.session = SessionManager(request.session, origin, msg).start_assessment()
                return Response(request.session['questionasked'], status=200)
            
            elif (request.session['input_tag'].endswith('booking') and msg.lower() == 'yes'):
                #start booking
                request.session = SessionManager(request.session, origin, msg).start_booking()
                return Response(request.session['booking_questions'], status=200)
          
            '''
            
            elif (request.session['questionasked'] == None and request.session['process'] != None and msg.lower() == 'yes'):
                #start process
                request.session = SessionManager(request.session, origin, msg).start_process()
                return Response(request.session['questionasked'], status=200)
            elif (request.session['questionasked'] == None and request.session['process']  != None and msg.lower() == 'no'):
                #kill process
                request.session = SessionManager(request.session, origin, msg).kill_process()
                return Response('Process Terminated', status=200)
            elif (request.session['questionasked'] != None and request.session['process'] != None):
                count = request.session['count']
                if count < len(request.session['questions']):
                    #continue the process
                    request.session = SessionManager(request.session, origin, msg).continue_process()
                    return Response(request.session['questionasked'], status=200)
                else:
                    #complete the process
                    request.session = SessionManager(request.session, origin, msg).complete_process()
                    return Response(request.session['event'], status=200)
            '''
        payload = model_builder(os.path.join(settings.MEDIA_ROOT, request.session['file']))  

        
        try: 
            output = get_response(msg,
                                    request.session['smart_funnel'],
                                    payload['model'], 
                                    payload['all_words'], 
                                    payload['tags'],
                                    request.session['intents'],
                                    torch.device('cpu')
                                    )
               
            status_code = 200 
            if output['input_tag'] is None:
                return Response(output['response'], status=status_code)
            else:
                request.session['input_tag'] = output['input_tag']
                csrf_token = get_token(request)
                response = Response(output['response'], status=status_code)  
                response.set_cookie("csrftoken", csrf_token)
                #response['X-Session-ID'] = request.session.session_key
                
                return response
        
        except:
            pass
        output = 'Im sorry. I dont have the answer now. Try again later, Im constantly learning and might be able to answer your question later.'
        return Response(output, status=200)
        
    
        
'''
@method_decorator(ensure_csrf_cookie, name='dispatch')
class GetCSRFTokenView(GenericAPIView):
    permission_classes = (permissions.AllowAny, )
    def get(self, request, format=None):
        csrf_token = get_token(request)
        return Response({'csrf_token': csrf_token})
        
'''
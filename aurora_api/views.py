from django.shortcuts import render
from django.http import HttpResponse, StreamingHttpResponse

from rest_framework import generics, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from .forms import ModelTrainingForm
from django.views import View
from .prediction_train import ModelTrainingObject
from .prediction_model import NeuralNet
from .models import Models, Customer, Image
import random, string 
import torch
from .extract import ModelIngredients, get_response, files_downloader
from .sessionsmanager import SessionManager, SessionEncrypt
from .nltk_utils import tokenize, bag_of_words
from .serializers import MsgSerializer, GetClientSerializer, ImageSerializer
from django.urls import reverse_lazy
import os
import atexit
from django.conf import settings
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
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
from django.core.signing import Signer
import base64
from cryptography.fernet import Fernet
from .tasks import test_func
from langchain.chains import RetrievalQAWithSourcesChain, ConversationalRetrievalChain 
from langchain.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnableMap
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI, VertexAI 
from langchain.chat_models import ChatOpenAI
import pickle
from langchain.schema import retriever
import os
from django.conf import settings
import faiss
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
import time
import re
from rest_framework.response import Response


class TestAPIView(GenericAPIView):
    def get(self, request):
        test_func.delay()
        return HttpResponse('Done')


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
    encryption_key = Fernet.generate_key()
    bag = ''
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data) 
        
        if serializer.is_valid():
            msg  = serializer.data['msg'] if serializer.data['msg'] is not None else 'Progress Chat'
            key = serializer.data['session_key']
            image = serializer.validated_data.get('image_upload')
            origin = serializer.data.get('origin', request.META.get('HTTP_ORIGIN', None))
            print(origin,'here')
    
        if key == '':
            session = SessionManager(origin).create_session()
            
            key = session.session_key
            session['session_key'] = key
            session.save()
            #Create custom session here
 
        else:
            #Pull from custom session here
            session = SessionStore(session_key=key)
            session['session_key'] = key
            session.save()
        
        files_downloader(session['customer_name'])
        

        try: 
            output = get_response(msg,session)
        except Exception as e:
            print('failed')
            output = "Im sorry. I dont have the answer now. Try again later, Im constantly learning and might be able to answer your question later."
        
        data = {
                'session_key': key,
                'response': output
            }
       
        '''
        def event_stream():
            for chunk in get_response(msg,payload['model'],payload['all_words'],payload['tags'],session,torch.device('cpu')):
                data = {"session_key": key, "response": chunk}
                yield data
        
        response = StreamingHttpResponse(event_stream(), content_type='application/json', status=200)
        response['X-Accel-Buffering'] = 'no'  # Disable buffering in nginx
        response['Cache-Control'] = 'no-cache'  # Ensure clients don't cache the 

        #time.sleep(1.5)
        data = {
            "session_key": key,
            "response": response
        }
        '''
        return Response(data)
        

class ImageUploadAPI(APIView):
    serializer_class = ImageSerializer
    def post(self, request, *args, **kwargs):
        origin = request.META['HTTP_ORIGIN']
        customer = Customer.objects.get(origin=origin)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            image_upload = serializer.validated_data.get('image_upload')
            session_key = serializer.data.get('session_key')


        return Response('Image Uploaded Successfully')
        
            
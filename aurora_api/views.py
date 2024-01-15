from django.shortcuts import render
from django.http import HttpResponse, StreamingHttpResponse
from rest_framework import generics, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from django.views import View
from .models import Customer, Models, RateLimitSetting
import random, string 
import torch
from .extract import ModelIngredients, get_response, files_downloader
from .sessionsmanager import SessionManager, SessionEncrypt
from .serializers import MsgSerializer, GetClientSerializer
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
from django.core.cache import cache 
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator



class TestAPIView(GenericAPIView):
    def get(self, request):
        test_func.delay()
        return HttpResponse('Done')


class ModelResponseAPI(APIView):
    '''Main API which user requests will hit and returns a response to their questions'''
    serializer_class = MsgSerializer
    encryption_key = Fernet.generate_key()
    bag = ''
    
    #RATE_LIMIT_KEY = 'Southend_Council' 
    
    @staticmethod
    def get_rate_limit_setting():
        #cache.clear()
        rate_limit_setting = cache.get('rate_limit_setting')
        
        if rate_limit_setting is None:
            try:
                rate_limit_setting = RateLimitSetting.objects.get(key='Southend Council')
            except RateLimitSetting.DoesNotExist:
                rate_limit_setting = RateLimitSetting(limit=500, interval='day', key='Southend Council')
                rate_limit_setting.save()
            cache.set('rate_limit_setting', rate_limit_setting, timeout=3600)
        print(f"Southend API Rate Limit: {rate_limit_setting.limit}/{rate_limit_setting.interval}")
        return f"{rate_limit_setting.limit}/{rate_limit_setting.interval}"
        
        
    
    @(method_decorator(ratelimit(key='ip', rate=get_rate_limit_setting(), block=True))) 
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data) 
        
        if serializer.is_valid():
            msg  = serializer.data['msg'] if serializer.data['msg'] is not None else 'Progress Chat'
            key = serializer.data['session_key']
            image = serializer.validated_data.get('image_upload')
            origin = serializer.data.get('origin', request.META.get('HTTP_ORIGIN', None))
          

    
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
     
        return Response(data)
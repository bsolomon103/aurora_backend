from django.test import TestCase
from .models import Models
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
import torch

User = get_user_model()

class GetResponseTest(TestCase):

    def setUp(self):
        print('Test setting up')

    def check_cuda(self):
        device = torch.cuda.is_available()
        if device == True:
            print("GPU is available")
        else:
            print("GPU is not available")

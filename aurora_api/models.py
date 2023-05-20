from django.db import models
from django.conf import settings
import os


class Customer(models.Model):
    name = models.CharField(max_length=50, null=False)


class Models(models.Model):
    customer_name = models.ForeignKey('Customer', on_delete=models.CASCADE, null=False)
    intent = models.JSONField(null=False)
    smart_funnel = models.CharField(max_length=5, default='False')
    training_file = models.FileField(upload_to='training_file', null=True, unique=True)
    model_key = models.CharField(max_length=200, unique=True, null=True)
    tokens = models.FileField(upload_to='tokens', null=True, max_length=200)
    origin = models.CharField(max_length=200, unique=True, null=True)
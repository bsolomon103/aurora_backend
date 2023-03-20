from django.db import models
from django.conf import settings
import os


class Customer(models.Model):
    name = models.CharField(max_length=50, null=False)


class Models(models.Model):
    customer_name = models.ForeignKey('Customer', on_delete=models.CASCADE, null=False)
    intent = models.JSONField(null=False)
    training_file = models.FilePathField(path = os.path.join(settings.BASE_DIR,'files'), null=True, unique=True)
    model_key = models.CharField(max_length=200, unique=True, null=True)
















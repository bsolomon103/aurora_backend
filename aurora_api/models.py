from django.db import models
from django.conf import settings
import os
from django.contrib.sessions.models import Session


class Treatments(models.Model):
    customer_name = models.ForeignKey('Customer', on_delete=models.CASCADE, null=False)
    treatment = models.CharField(max_length=200, unique=True, null=True)
    description = models.TextField(null=True)
    
    def __str__(self):
        return self.treatment
    

class Customer(models.Model):
    name = models.CharField(max_length=50, null=False)
    calendar_id = models.CharField(max_length=50, null=True)
    origin = models.CharField(max_length=200, unique=True, null=True)
    booking_questions = models.JSONField(null=True)
    mappings = models.JSONField(null=True)
    products = models.ManyToManyField(Treatments, through='TreatmentSeller')
    
    def __str__(self):
        return self.name

class TreatmentSeller(models.Model):
    product = models.ForeignKey(Treatments, on_delete=models.CASCADE)
    seller = models.ForeignKey(Customer, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.product} - {self.seller}"


class Price(models.Model):
    product_seller = models.ForeignKey(TreatmentSeller, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=250, null=True)

class Models(models.Model):
    customer_name = models.ForeignKey('Customer', on_delete=models.CASCADE, null=False)
    intent = models.JSONField(null=False)
    training_file = models.FileField(upload_to='training_file', null=True, unique=True)
    model_key = models.CharField(max_length=200, unique=True, null=True)

class AppCredentials(models.Model):
    google_secret = models.FileField(upload_to='secrets_file', null=True, unique=True)
    platform = models.CharField(max_length=250, null=True)
    
class Image(models.Model):
    name = models.CharField(max_length=250)
    image_file = models.ImageField(upload_to='images/', null=True, unique=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE, null=False)
    
    def __str__(self):
        return self.name
    
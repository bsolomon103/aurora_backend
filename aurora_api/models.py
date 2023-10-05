from django.db import models
from django.conf import settings
import os
from django.contrib.sessions.models import Session


class Treatments(models.Model):
    customer_name = models.ForeignKey('Customer', on_delete=models.CASCADE, null=False)
    treatment = models.CharField(max_length=200, unique=False, null=True)
    description = models.TextField(null=True)
    booking_duration = models.IntegerField(null=True)
    calendar_id = models.CharField(max_length=200, null=True)
    
    def __str__(self):
        return self.treatment
    

class Customer(models.Model):
    name = models.CharField(max_length=50, null=False)
    calendar_id = models.CharField(max_length=50, null=True)
    origin = models.CharField(max_length=200, unique=True, null=True)
    booking_questions = models.JSONField(null=True)
    mappings = models.JSONField(null=True)
    products = models.ManyToManyField(Treatments, through='TreatmentSeller')
    phone_number = models.CharField(max_length=15, null=True)
    email = models.CharField(max_length=150, null=True)
    closing = models.JSONField(null=True)
    treatment_init = models.JSONField(null=True)
    
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

class Booking(models.Model):
    booking_date = models.CharField(max_length=50)
    patient_name = models.CharField(max_length=50)
    patient_email = models.CharField(max_length=250, null=True)
    patient_phone = models.CharField(max_length=15, null=True)
    practise_name = models.CharField(max_length=250, null=True)
    practise_email = models.CharField(max_length=250, null=True)
    practise_phone = models.CharField(max_length=15, null=True)
    treatment = models.CharField(max_length=250, null=True)
    summary = models.JSONField(null=True)
    booking_status = models.CharField(max_length=50, default='unpaid')
    price = models.IntegerField(default=1)
    calendar_id = models.CharField(max_length=100, default= '')
    sessionid = models.CharField(max_length=100, null=True)
    booking_duration = models.IntegerField(default=15)
    setting = models.CharField(max_length=100, null=True)


class Payment(models.Model):
    name = models.CharField(max_length=250, null=True)
    amount = models.IntegerField()
    email = models.CharField(max_length=250, null=False)
    dob = models.DateField()


class Chat(models.Model):
   session_id = models.CharField(max_length=50)
   message = models.TextField(max_length=250)
   response = models.TextField(max_length=250)
   rating = models.CharField(max_length=5, null=True)
    
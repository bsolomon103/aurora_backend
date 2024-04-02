from django.db import models
from django.conf import settings
from django.utils import timezone
import os
import pytz
import boto3
from django.contrib.sessions.models import Session
from django.forms.models import model_to_dict
#from .custom_fields import S3FileField

'''
class Treatments(models.Model):
    customer_name = models.ForeignKey('Customer', on_delete=models.CASCADE, null=False)
    treatment = models.CharField(max_length=200, unique=False, null=True)
    description = models.TextField(null=True)
    booking_duration = models.IntegerField(null=True)
    calendar_id = models.CharField(max_length=200, null=True)
    
    def __str__(self):
        return self.treatment
'''
    

class Customer(models.Model):
    name = models.CharField(max_length=50, null=False)
    calendar_id = models.CharField(max_length=50, null=True)
    origin = models.CharField(max_length=200, unique=True, null=True)
    mappings = models.JSONField(null=True)
    phone_number = models.CharField(max_length=15, null=True)
    email = models.CharField(max_length=150, null=True)
    closing = models.JSONField(null=True)
    
    def __str__(self):
        return self.name

class RateLimitSetting(models.Model):
    key = models.CharField(max_length=255, unique=True)
    limit = models.PositiveIntegerField()
    interval = models.CharField(max_length=20)
    
    def __str__(self):
        return f"{self.key} - {self.limit}/{self.interval}"
        
        
'''
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
'''

class Chat(models.Model):
   session_id = models.CharField(max_length=50)
   message = models.TextField(max_length=250)
   response = models.TextField(max_length=250)
   chats = models.IntegerField(default=1, blank=False)
   human_agent = models.BooleanField(default=False)
   intent = models.CharField(max_length=50, null=True)
   reason = models.CharField(max_length=50, null=True)
   created_at = models.DateTimeField(default=timezone.now)
   
   '''
   def save(self, *args, **kwargs):
        # Set the timezone to Europe/London
        london_tz = timezone.pytz.timezone('Europe/London')
        created_at = timezone.datetime.now(london_tz)
        self.created_at = created_at
        super().save(*args, **kwargs)
    '''
    
   
    

#Extend filefield attribute to upload to S3
class S3FileField(models.FileField):
    def generate_filename(self, instance, filename):
        #Use customer name to create filename
        if filename:
            ext = os.path.splitext(filename)[1] if os.path.splitext(filename)[1] else None
            attributes = model_to_dict(instance)
            if 'customer_name' in attributes:
                filename = f"{instance.customer_name}{ext}"
            if 'platform' in attributes:
                filename = f"{instance.platform}{ext}"
            print(filename)
            return filename
        #else:
            #return 'southend council.pth'

    def upload_to(self, instance, filename):
        x = f"{os.environ['AWS_STORAGE_BUCKET_NAME']}/{self.generate_filename(instance, filename)}"
        print(x)
        return x

    def get_s3_url(self, instance, filename):
        s3 = boto3.client('s3', region_name='eu-west-2')
        #s3_filename = self.upload_to(instance, filename)
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': os.environ['AWS_STORAGE_BUCKET_NAME'], 
                    'Key': filename},
            ExpiresIn=3600  # URL expiration time in seconds
        )
        return url
        
        
#Use custom S3FileField in Models object
class Models(models.Model):
    customer_name = models.ForeignKey('Customer', on_delete=models.CASCADE, null=False)
    intent = models.JSONField(null=False)
    training_file = S3FileField(upload_to='upload_to', null=True, unique=True)
    model_key = models.CharField(max_length=200, unique=True, null=True)

class AppCredentials(models.Model):
    google_secret = S3FileField(upload_to='upload_to', null=True, unique=True)
    platform = models.CharField(max_length=250, null=True)
    

class HumanContact(models.Model):
    service = models.CharField(max_length=25, null=False)
    request = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    
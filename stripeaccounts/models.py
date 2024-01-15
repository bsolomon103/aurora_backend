'''
from django.db import models
from aurora_api.models import Customer

class StripeInfo(models.Model):
      customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
      product_description = models.CharField(max_length=140)
      mcc = models.CharField(max_length=5)
      phone = models.CharField(max_length=13)
      verified = models.BooleanField(default=False)
      account_id = models.CharField(max_length=250, null=True)
'''
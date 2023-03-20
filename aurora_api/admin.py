from django.contrib import admin
from .models import Models, Customer

admin.site.register(Customer)
admin.site.register(Models)

from django.contrib import admin
from .models import StripeInfo


class StripeInfoAdmin(admin.ModelAdmin):
    list_display = ['customer']
    
admin.site.register(StripeInfo,StripeInfoAdmin)



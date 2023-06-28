from django.contrib import admin
from .models import Models, Customer, AppCredentials, Treatments, Price, TreatmentSeller



class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name']

class ModelAdmin(admin.ModelAdmin):
    list_display = ['customer_name']

class TreatmentAdmin(admin.ModelAdmin):
    list_display = ['treatment', 'customer_name']
    

class PriceAdmin(admin.ModelAdmin):
    list_display = ['description', 'product_seller', 'quantity','price']

class TreatmentSellerAdmin(admin.ModelAdmin):
    list_display = ['product', 'seller']

class AppCredentialsAdmin(admin.ModelAdmin):
    list_display = ['platform']

admin.site.register(Customer, CustomerAdmin)
admin.site.register(Models, ModelAdmin)
admin.site.register(AppCredentials, AppCredentialsAdmin)
admin.site.register(Treatments, TreatmentAdmin)
admin.site.register(Price, PriceAdmin)
admin.site.register(TreatmentSeller, TreatmentSellerAdmin)


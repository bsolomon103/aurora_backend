from django.contrib import admin
from .models import Models, Customer, AppCredentials, Chat, RateLimitSetting, HumanContact
#Treatments, Price, TreatmentSeller, Booking, Chat


class ChatAdmin(admin.ModelAdmin):
    list_display = ['id', 'session_id', 'message', 'response', 'chats','human_agent', 'intent', 'reason', 'created_at']
    
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name']

class ModelAdmin(admin.ModelAdmin):
    list_display = ['customer_name']

class RateLimitAdmin(admin.ModelAdmin):
    list_display = ['key', 'limit', 'interval']
    
class HumanContactAdmin(admin.ModelAdmin):
    list_display = ['service', 'request', 'created_at']

'''
class TreatmentAdmin(admin.ModelAdmin):
    list_display = ['treatment', 'customer_name']
    

class PriceAdmin(admin.ModelAdmin):
    list_display = ['description', 'product_seller', 'quantity','price']

class TreatmentSellerAdmin(admin.ModelAdmin):
    list_display = ['product', 'seller']

class AppCredentialsAdmin(admin.ModelAdmin):
    list_display = ['platform']
    
class BookingAdmin(admin.ModelAdmin):
    list_display = ['treatment','patient_name','practise_name','practise_email','patient_email','patient_phone','booking_date','price','booking_status', 'booking_duration','setting']

'''
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Models, ModelAdmin)
admin.site.register(RateLimitSetting, RateLimitAdmin)
#admin.site.register(AppCredentials, AppCredentialsAdmin)
#admin.site.register(Treatments, TreatmentAdmin)
#admin.site.register(Price, PriceAdmin)
#admin.site.register(TreatmentSeller, TreatmentSellerAdmin)
#admin.site.register(Booking, BookingAdmin)
admin.site.register(Chat, ChatAdmin)
admin.site.register(HumanContact, HumanContactAdmin)

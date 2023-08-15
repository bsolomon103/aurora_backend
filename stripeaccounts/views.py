from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpResponse as Response, JsonResponse
import webbrowser
from django.urls import reverse_lazy
from .forms import StripeForm
import stripe
from .models import StripeInfo
from aurora_api.models import  Customer, Price, TreatmentSeller, Booking, Treatments
from .models import StripeInfo
from rest_framework.views import APIView
from .serializers import KeySerializer
from cryptography.fernet import Fernet
from django.contrib.sessions.backends.db import SessionStore
from aurora_api.sessionsmanager import SessionManager, SessionEncrypt
from .verification import check_verified
import json
from aurora_api.task_utils import create_event
from aurora_api.booking import update_create_event, update_failed_event
#stripe.api_key = "sk_test_51NJcbbD1RPWlDlnhXqjIuP8aAsbR3u08EO83FB2FHpfhG8nCgsUbD0fWolN5ifoptsh3ZZsKwOPHzHf1z4P1spU900V7doveLa"
#endpoint_secret = 'whsec_oNUBClYDh4XalAth8xIZQBpS6ceMMp4i'
import os 
from django.db.models import Q



class SuccessPage(View):
    template = 'components/success.html'
    def get(self, request, *args, **kwargs):
        return render(request, self.template)

class CreateView(View):
    template = 'components/stripeform.html'
    def get(self, request, *args, **kwargs):
        form = StripeForm()
        ctx = {'form': form}
        return render(request, self.template, context=ctx)
    
    def post(self, request, *args, **kwargs):
        origin = request.META['HTTP_ORIGIN']
        if origin == 'http://18.133.125.44:8080/':
            stripe.api_key = os.environ['TEST_STRIPE_KEY']
        
        form = StripeForm(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data['name']
            description = form.cleaned_data['description']
            mcc = form.cleaned_data['mcc']
            phone = form.cleaned_data['phone']
            
            try:
                account = stripe.Account.create(
                          country="GB",
                          type="express",
                          capabilities={"card_payments": {"requested": True}, "transfers": {"requested": True}},
        
                          business_profile={"product_description": description,
                                            "mcc" : mcc,
                                            "support_phone" : phone,
                                            "name" : name
                          },
                          )
                
                idx = account['id']
        
                customer_obj = Customer.objects.get(name=name)
                qs = StripeInfo.objects.filter(customer = customer_obj)
                #Make sure customer doesn't already have an account
                if len(qs) == 0:
                    StripeInfo.objects.create(
                    customer = customer_obj,
                    product_description = description,
                    mcc = mcc,
                    phone = phone,
                    account_id = idx
                    )
                    print('Account created successfully not verified')
                    
                    #Once account created successfully redirect to link to verify
                    account_link = stripe.AccountLink.create(
                                account=idx,
                                refresh_url="https://example.com/reauth",
                                return_url="https://example.com/return",
                                type="account_onboarding",
                                )
                    link = account_link['url']
                    return redirect(link)
                else:
                    return Response('Customer already has an account')
            except Exception as e:
                print(e)
                return Response(f"No matching customer found for {name}")
                
                
# The test API key locks the platform to the us so can only test in USD
# Once you move to production keys you can create charges in GBP

class CheckOutView(APIView):
    serializer_class = KeySerializer
    encryption_key = Fernet.generate_key()
    
    def post(self, request, *args, **kwargs):
        origin = request.META['HTTP_ORIGIN']
        if origin == 'http://35.178.231.126:8080/':
            stripe.api_key = os.environ['TEST_STRIPE_KEY']
            
        serializer = self.serializer_class(data=request.data) 
        if serializer.is_valid():
            key = serializer.data['session_key']
            session = SessionStore(session_key=key)
            booking_date = session['summary']['booking_date']
            patient_name = session['summary']['client name']
            patient_email = session['summary']['email']
            patient_phone = session['summary']['phone']
            #Consider getting booking category from booking category instead of treatment category
            treatment = session['summary']['treatment category'].title()
            print(treatment)
            #Add code here to map treatment to priceable treatments
        
            summary = session['summary']
            practise_name = session['customer_name']
            calendar_id = session['calendar_id']
            session_id = session['session_key']
            booking_status = 'unpaid'
            practise_obj = Customer.objects.get(name=practise_name)
            #practise_email = practise_obj.email
            practise_phone = practise_obj.phone_number
            quantity = session['summary']['quantity desired'] if 'quantity desired' in session['summary'] else 1

            treatment_obj = Treatments.objects.get(customer_name=practise_obj, treatment=treatment)
            practise_email = treatment_obj.calendar_id
            booking_duration = treatment_obj.booking_duration
            
            

            practise_id = session['customer_id'] 
            treatment_seller_obj = TreatmentSeller.objects.filter(seller_id=practise_id)
            
            for s in treatment_seller_obj:
                if (s.product.treatment == session['booking_category'].title()):
                    product_seller_obj = s
            price = Price.objects.get(product_seller=product_seller_obj, quantity=quantity).price * 100
            booking = Booking.objects.create(
                booking_date = booking_date,
                patient_name = patient_name,
                patient_email = patient_email,
                patient_phone = patient_phone,
                practise_name = practise_name,
                practise_email = practise_email,
                practise_phone = practise_phone,
                treatment = treatment,
                summary = summary,
                booking_status = booking_status,
                price = price/100,
                calendar_id = calendar_id, 
                sessionid = session_id,
                booking_duration = booking_duration
                )
            
            
            stripeinfobj = StripeInfo.objects.get(customer_id=practise_id)
            if stripeinfobj.verified == False:
                if not check_verified(stripeinfobj.account_id):
                    data = {'message': 'Account has not been verified yet'}
                    return JsonResponse(data, status=200)
                else:
                    stripeinfobj.verified = True
                    stripeinfobj.save()
                    print('Stripe account has been verified')
            
            
            checkoutsession = stripe.checkout.Session.create(
                line_items=[{
                        'price_data': {
                        'currency': 'gbp', #remember to change to gbp in prod.
                        'product_data': {
                                    'name': f"{quantity} * {session['booking_category'].title()}",
                        },
                        'unit_amount': int(price),
                        },
                        'quantity': 1,
                        }],
                        mode='payment',
                        success_url='https://api.eazibots.com/stripeaccounts/success-page/',
                        cancel_url='http://localhost:4242/cancel',
                        customer_email = patient_email,
                        payment_intent_data={
                            #'application_fee_amount': 0,  # Set the application fee for the connected account
                            'transfer_data': {
                            #'destination': stripeinfobj.account_id,  # Specify the connected account ID
                            },
                        },
                     )
                     
            data = {'checkout_url': checkoutsession.url}
            #print(checkoutsession.id)
            return JsonResponse(data, status=200)

class PaymentCompleteAPI(APIView):
    def post(self, request, *args, **kwargs):
        stripe.api_key = os.environ['TEST_STRIPE_KEY'] #change to live keys
            
        event = None
        payload = request.body
        endpoint_secret = os.environ['WEBHOOK_SECRET']
        sig_header = request.headers['STRIPE_SIGNATURE']
        
        try:
            event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret)
            #print(event)
        except ValueError as e:
            #invalid payload
            print(str(e))
            return Response(str(e))
        
        except stripe.error.SignatureVerificationError as e:
            #invalid signature
            print(str(e))
            return Response(str(e))
        
        # Handle the event
    
        if event['type'] == 'checkout.session.async_payment_failed':
            session = event['data']['object']
            user_email = session['customer_details']['email']
            user_name = session['customer_details']['name']
            update_failed_event(user_name, user_email)
            
        elif event['type'] == 'checkout.session.async_payment_succeeded':
            session = event['data']['object']
            user_email = session['customer_details']['email']
            user_name = session['customer_details']['name']
            booking_obj = Booking.objects.filter((Q(user_name__icontains=user_name) & Q(booking_status='unpaid')) |
            (Q(email__contains=user_email) & Q(booking_status='unpaid')))
            booking_obj = list(booking_obj)
            obj = booking_obj[-1]
            #obj.phone
            update_create_event(user_name, user_email)
            
        elif event['type'] == 'checkout.session.completed':
          session = event['data']['object']
          user_email = session['customer_details']['email']
          user_name = session['customer_details']['name']
          update_create_event(user_name, user_email)
          
        elif event['type'] == 'checkout.session.expired':
          session = event['data']['object']
        # ... handle other event types
        else:
          print('Unhandled event type {}'.format(event['type']))
        return Response({'success':True})
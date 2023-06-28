from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpResponse as Response, JsonResponse
import webbrowser
from django.urls import reverse_lazy
from .forms import StripeForm
import stripe
from .models import StripeInfo
from aurora_api.models import  Customer, Price, TreatmentSeller
from .models import StripeInfo
from rest_framework.views import APIView
from .serializers import KeySerializer
from cryptography.fernet import Fernet
from django.contrib.sessions.backends.db import SessionStore
from aurora_api.sessionsmanager import SessionManager, SessionEncrypt
from .verification import check_verified
stripe.api_key = "sk_test_4eC39HqLyjWDarjtT1zdp7dc"


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
        serializer = self.serializer_class(data=request.data) 
        if serializer.is_valid():
            key = serializer.data['session_key']
            session = SessionStore(session_key=key)
            quantity = session['summary']['quantity'] if 'quantity' in session['summary'] else 1
            
            seller_id = session['customer_id'] 
            treatment_seller_obj = TreatmentSeller.objects.filter(seller_id=seller_id)
            
            for s in treatment_seller_obj:
                if s.product.treatment == session['booking_category'].title():
                    product_seller_obj = s
            price = Price.objects.get(product_seller=product_seller_obj, quantity=quantity).price * 100
            stripeinfobj = StripeInfo.objects.get(customer_id=seller_id)
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
                        'currency': 'usd', #remember to change to gbp in prod.
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
                        payment_intent_data={
                            #'application_fee_amount': 0,  # Set the application fee for the connected account
                            'transfer_data': {
                            #'destination': stripeinfobj.account_id,  # Specify the connected account ID
                            },
                        },
                     )
        
         
            data = {'checkout_url': checkoutsession.url}
            print(checkoutsession.id)
            return JsonResponse(data, status=200)
        
    
    

       

        
       
        
        
        
    
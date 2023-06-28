from django.urls import path, include
from .views import CreateView, CheckOutView, SuccessPage

app_name = 'stripe'
urlpatterns = [
    path('createaccount/', CreateView.as_view(), name='createaccount'),
    path("create-checkout-session/", CheckOutView.as_view(), name='checkout'),
    path("success-page/", SuccessPage.as_view(), name='success-page'),
    ]
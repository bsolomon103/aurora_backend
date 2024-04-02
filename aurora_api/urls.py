from django.urls import path, include
from .views import  ModelResponseAPI, TestAPIView, ContactView

app_name = 'apis'
urlpatterns = [
    path('', TestAPIView.as_view()),
    path('contact-form/', ContactView.as_view()),
    path('response/', ModelResponseAPI.as_view()),
]
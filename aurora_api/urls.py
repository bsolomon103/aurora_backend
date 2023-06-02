from django.urls import path, include
from .views import  ModelTrainingView, ModelResponseAPI, TestAPIView
#, GetCSRFTokenView

app_name = 'apis'
urlpatterns = [
    path('', TestAPIView.as_view()),
    path('training/', ModelTrainingView.as_view(), name='training'),
    path('response/', ModelResponseAPI.as_view()),
 #   path('csrf_cookie/', GetCSRFTokenView.as_view())
 
]
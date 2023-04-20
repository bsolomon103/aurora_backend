from django.urls import path, include
from .views import  ModelTrainingView, ModelResponseAPI, GetCSRFTokenView

app_name = 'apis'
urlpatterns = [
    #path('', TestAPIView.as_view()),
    path('training/', ModelTrainingView.as_view(), name='training'),
    path('response/', ModelResponseAPI.as_view()),
    path('get_token/', GetCSRFTokenView.as_view())
 
]
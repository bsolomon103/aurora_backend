from django.urls import path, include
from .views import  ModelTrainingView, ModelResponseAPI

app_name = 'apis'
urlpatterns = [
    #path('', TestAPIView.as_view()),
    path('training/', ModelTrainingView.as_view(), name='training'),
    path('response/', ModelResponseAPI.as_view())

]
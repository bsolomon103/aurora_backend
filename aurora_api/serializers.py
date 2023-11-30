from rest_framework import serializers
from .models import Image

class MsgSerializer(serializers.Serializer):
    msg = serializers.CharField()
    session_key = serializers.CharField(allow_blank=True, required=False)
    image_upload = serializers.ImageField(required=False)
    origin = serializers.CharField(allow_blank=True, required=False)

class ImageSerializer(serializers.Serializer):
    image_upload = serializers.ImageField(required=True)
    
class GetClientSerializer(serializers.Serializer):
    origin = serializers.CharField()

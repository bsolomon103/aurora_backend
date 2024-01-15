from rest_framework import serializers


class MsgSerializer(serializers.Serializer):
    msg = serializers.CharField()
    session_key = serializers.CharField(allow_blank=True, required=False)
    image_upload = serializers.ImageField(required=False)
    origin = serializers.CharField(allow_blank=True, required=False)


    
class GetClientSerializer(serializers.Serializer):
    origin = serializers.CharField()

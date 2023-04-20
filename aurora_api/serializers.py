from rest_framework import serializers

class MsgSerializer(serializers.Serializer):
    msg = serializers.CharField()

class GetClientSerializer(serializers.Serializer):
    origin = serializers.CharField()

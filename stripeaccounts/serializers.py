from rest_framework import serializers

class KeySerializer(serializers.Serializer):
    session_key = serializers.CharField(allow_blank=False, required=True)
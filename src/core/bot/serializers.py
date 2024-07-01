from rest_framework import serializers
from core.bot.models import MessageText


class MessageTextSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageText
        fields = '__all__'

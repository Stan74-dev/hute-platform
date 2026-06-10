from rest_framework import serializers
from .models import Currency, ExchangeRate, SplitTender, SplitTenderLine
class CurrencySerializer(serializers.ModelSerializer):
    class Meta: model = Currency; fields = "__all__"
class ExchangeRateSerializer(serializers.ModelSerializer):
    class Meta: model = ExchangeRate; fields = "__all__"
class SplitTenderLineSerializer(serializers.ModelSerializer):
    class Meta: model = SplitTenderLine; fields = "__all__"
class SplitTenderSerializer(serializers.ModelSerializer):
    lines = SplitTenderLineSerializer(many=True, read_only=True)
    class Meta: model = SplitTender; fields = "__all__"

from rest_framework import serializers
from .models import PaymentTransaction

class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = "__all__"
        read_only_fields = ["status", "raw_response", "created_by", "created_at", "updated_at"]

class PaymentInitiateSerializer(serializers.Serializer):
    provider = serializers.ChoiceField(choices=["ecocash", "innbucks", "mukuru", "zipit", "cash", "card"])
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    currency = serializers.CharField(default="USD")
    customer_phone = serializers.CharField(required=False, allow_blank=True)

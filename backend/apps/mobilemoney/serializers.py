from rest_framework import serializers
from .models import MobileMoneyRequest
class MobileMoneyRequestSerializer(serializers.ModelSerializer):
    class Meta: model = MobileMoneyRequest; fields = "__all__"; read_only_fields = ["status","internal_reference","provider_reference","request_payload","response_payload","callback_payload","created_by","created_at","updated_at"]
class CreateMobileMoneyRequestSerializer(serializers.Serializer):
    provider=serializers.ChoiceField(choices=["ecocash","innbucks","mukuru","zipit"])
    amount=serializers.DecimalField(max_digits=14, decimal_places=2)
    currency=serializers.CharField(default="USD")
    customer_phone=serializers.CharField()
    sale_id=serializers.IntegerField(required=False)

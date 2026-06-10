from rest_framework import serializers
from .models import FiscalDevice, FiscalInvoice, FiscalSubmissionLog
class FiscalDeviceSerializer(serializers.ModelSerializer):
    class Meta: model = FiscalDevice; fields = "__all__"
class FiscalInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FiscalInvoice
        fields = "__all__"
        read_only_fields = ["created_by", "created_at", "submitted_at"]
class FiscalSubmissionLogSerializer(serializers.ModelSerializer):
    class Meta: model = FiscalSubmissionLog; fields = "__all__"

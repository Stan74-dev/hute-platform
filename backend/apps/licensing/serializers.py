from rest_framework import serializers
from .models import SubscriptionPlan,Tenant,Subscription,LicenseKey
class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta: model=SubscriptionPlan; fields="__all__"
class TenantSerializer(serializers.ModelSerializer):
    class Meta: model=Tenant; fields="__all__"
class SubscriptionSerializer(serializers.ModelSerializer):
    is_valid=serializers.BooleanField(read_only=True)
    class Meta: model=Subscription; fields="__all__"
class LicenseKeySerializer(serializers.ModelSerializer):
    class Meta: model=LicenseKey; fields="__all__"

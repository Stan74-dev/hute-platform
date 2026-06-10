from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import SubscriptionPlan,Tenant,Subscription,LicenseKey
from .serializers import SubscriptionPlanSerializer,TenantSerializer,SubscriptionSerializer,LicenseKeySerializer
class SubscriptionPlanViewSet(viewsets.ModelViewSet): queryset=SubscriptionPlan.objects.all(); serializer_class=SubscriptionPlanSerializer; permission_classes=[permissions.IsAuthenticated]
class TenantViewSet(viewsets.ModelViewSet): queryset=Tenant.objects.all(); serializer_class=TenantSerializer; permission_classes=[permissions.IsAuthenticated]
class SubscriptionViewSet(viewsets.ModelViewSet): queryset=Subscription.objects.select_related("tenant","plan").all(); serializer_class=SubscriptionSerializer; permission_classes=[permissions.IsAuthenticated]
class LicenseKeyViewSet(viewsets.ModelViewSet): queryset=LicenseKey.objects.select_related("tenant").all(); serializer_class=LicenseKeySerializer; permission_classes=[permissions.IsAuthenticated]
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def current_license_status(request):
    s=Subscription.objects.filter(is_active=True).select_related("tenant","plan").order_by("-ends_at").first()
    if not s: return Response({"licensed":False,"message":"No active subscription found"})
    return Response({"licensed":s.is_valid,"tenant":s.tenant.business_name,"plan":s.plan.name,"ends_at":s.ends_at,"limits":{"branches":s.plan.max_branches,"users":s.plan.max_users,"terminals":s.plan.max_terminals},"features":{"fiscalisation":s.plan.has_fiscalisation,"mobile_money":s.plan.has_mobile_money,"multicurrency":s.plan.has_multicurrency}})

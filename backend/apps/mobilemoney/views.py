import os, uuid
from rest_framework import permissions, viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import MobileMoneyRequest
from .serializers import MobileMoneyRequestSerializer, CreateMobileMoneyRequestSerializer
class MobileMoneyRequestViewSet(viewsets.ReadOnlyModelViewSet): queryset=MobileMoneyRequest.objects.all(); serializer_class=MobileMoneyRequestSerializer; permission_classes=[permissions.IsAuthenticated]
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def initiate_mobile_money(request):
    s=CreateMobileMoneyRequestSerializer(data=request.data); s.is_valid(raise_exception=True); d=s.validated_data
    ref=f"HUTE-MM-{uuid.uuid4().hex[:12].upper()}"
    mm=MobileMoneyRequest.objects.create(provider=d["provider"], amount=d["amount"], currency=d.get("currency","USD"), customer_phone=d["customer_phone"], sale_id=d.get("sale_id"), internal_reference=ref, created_by=request.user)
    if os.environ.get("MOBILE_MONEY_MODE","sandbox")=="sandbox":
        mm.status="customer_prompted"; mm.provider_reference=f"SANDBOX-{ref}"; mm.response_payload={"message":"Sandbox customer prompt created"}
    else: mm.response_payload={"message":"Provider API credentials not configured yet"}
    mm.save(); return Response(MobileMoneyRequestSerializer(mm).data, status=status.HTTP_201_CREATED)
@api_view(["POST"])
def provider_callback(request, internal_reference):
    try: mm=MobileMoneyRequest.objects.get(internal_reference=internal_reference)
    except MobileMoneyRequest.DoesNotExist: return Response({"detail":"Request not found"}, status=404)
    mm.callback_payload=request.data
    if str(request.data.get("status","")).lower() in ["paid","success","successful"]: mm.status="paid"
    elif str(request.data.get("status","")).lower() in ["failed","declined"]: mm.status="failed"
    mm.save(); return Response({"ok":True,"status":mm.status})

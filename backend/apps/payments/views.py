import uuid
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import PaymentTransaction
from .serializers import PaymentTransactionSerializer, PaymentInitiateSerializer

class PaymentTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PaymentTransaction.objects.all()
    serializer_class = PaymentTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def initiate_payment(request):
    serializer = PaymentInitiateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    data = serializer.validated_data
    provider = data["provider"]
    tx = PaymentTransaction.objects.create(
        provider=provider,
        amount=data["amount"],
        currency=data.get("currency", "USD"),
        customer_phone=data.get("customer_phone", ""),
        internal_reference=f"HUTE-{uuid.uuid4().hex[:12].upper()}",
        created_by=request.user,
    )

    if provider in ["cash", "card"]:
        tx.status = "success"
        tx.raw_response = {"message": "Manual payment accepted"}
    else:
        tx.status = "pending"
        tx.raw_response = {"message": "Provider API not connected yet"}
    tx.save()

    return Response(PaymentTransactionSerializer(tx).data, status=status.HTTP_201_CREATED)

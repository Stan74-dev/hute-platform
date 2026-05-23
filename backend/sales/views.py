from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.accounts.permissions import IsAdminOrManager
from apps.inventory.models import Warehouse
from .models import Sale, SaleService
from .serializers import SaleSerializer, CreateSaleSerializer


class SaleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Sale.objects.select_related("warehouse", "cashier").prefetch_related("items__product").all()
    serializer_class = SaleSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAdminOrManager()]
        return super().get_permissions()

    def get_queryset(self):
        queryset = super().get_queryset()
        warehouse_id = self.request.query_params.get("warehouse")
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        return queryset

    @action(detail=False, methods=["post"])
    def checkout(self, request):
        serializer = CreateSaleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        warehouse = Warehouse.objects.get(id=serializer.validated_data["warehouse"])

        try:
            sale = SaleService.create_sale(
                warehouse=warehouse,
                cashier=request.user,
                payment_method=serializer.validated_data["payment_method"],
                items=serializer.validated_data["items"],
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)
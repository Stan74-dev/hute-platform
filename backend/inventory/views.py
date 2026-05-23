from django.db import transaction
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import PurchaseOrder, PurchaseOrderItem, GoodsReceivedNote, Stock


class GoodsReceiveView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        po_id = request.data.get("purchase_order")
        items = request.data.get("items", [])

        if not po_id:
            return Response({"detail": "Purchase order required"}, status=400)

        po = get_object_or_404(PurchaseOrder, id=po_id)

        grn = GoodsReceivedNote.objects.create(
            grn_number=f"GRN-{po.id}-{po.created_at.strftime('%Y%m%d%H%M%S')}",
            purchase_order=po,
            notes="Auto-generated from receiving",
        )

        for item in items:
            po_item_id = item.get("po_item_id")
            received_qty = float(item.get("received_qty", 0))

            if received_qty <= 0:
                continue

            po_item = get_object_or_404(PurchaseOrderItem, id=po_item_id)

            # UPDATE STOCK
            stock, _ = Stock.objects.get_or_create(
                product=po_item.product,
                warehouse=po.warehouse,
                defaults={"quantity": 0},
            )

            stock.quantity += received_qty
            stock.save()

        return Response({
            "detail": "Goods received successfully",
            "grn_id": grn.id
        })

from apps.accounts.utils import create_audit_log
from .models import (
    Product,
    Warehouse,
    Stock,
    Supplier,
    PurchaseOrder,
    PurchaseOrderItem,
    GoodsReceivedNote,
    StockTransfer,
)


class ProductListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        search = (request.GET.get("search") or "").strip()

        queryset = Product.objects.all().order_by("name")

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(sku__icontains=search)
                | Q(barcode__icontains=search)
            )

        return Response([
            {
                "id": product.id,
                "name": product.name,
                "sku": product.sku,
                "barcode": product.barcode,
                "description": product.description,
                "cost_price": str(product.cost_price),
                "selling_price": str(product.selling_price),
                "reorder_level": product.reorder_level,
                "is_active": product.is_active,
                "tax_rate": product.tax_rate_id,
                "tax_rate_name": product.tax_rate.name if getattr(product, "tax_rate", None) else "",
            }
            for product in queryset
        ])


class WarehouseListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Warehouse.objects.all().order_by("name")

        return Response([
            {
                "id": warehouse.id,
                "name": warehouse.name,
                "code": warehouse.code,
                "location": warehouse.location,
                "is_active": warehouse.is_active,
            }
            for warehouse in queryset
        ])


class SupplierListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        search = (request.GET.get("search") or "").strip()

        queryset = Supplier.objects.all().order_by("name")

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(contact_person__icontains=search)
                | Q(email__icontains=search)
                | Q(phone__icontains=search)
            )

        return Response([
            {
                "id": supplier.id,
                "name": supplier.name,
                "contact_person": supplier.contact_person,
                "email": supplier.email,
                "phone": supplier.phone,
                "address": supplier.address,
                "is_active": supplier.is_active,
            }
            for supplier in queryset
        ])


class StockListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        warehouse_id = (request.GET.get("warehouse") or "").strip()
        product_id = (request.GET.get("product") or "").strip()
        search = (request.GET.get("search") or "").strip()

        queryset = Stock.objects.select_related("product", "warehouse").all().order_by(
            "warehouse__name",
            "product__name",
        )

        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)

        if product_id:
            queryset = queryset.filter(product_id=product_id)

        if search:
            queryset = queryset.filter(
                Q(product__name__icontains=search)
                | Q(product__sku__icontains=search)
                | Q(warehouse__name__icontains=search)
            )

        return Response([
            {
                "id": stock.id,
                "product_id": stock.product_id,
                "product_name": stock.product.name if stock.product else "",
                "product_sku": stock.product.sku if stock.product else "",
                "warehouse_id": stock.warehouse_id,
                "warehouse_name": stock.warehouse.name if stock.warehouse else "",
                "quantity": stock.quantity,
                "updated_at": stock.updated_at,
            }
            for stock in queryset
        ])


class StockTransferListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = (
            StockTransfer.objects
            .select_related("product", "from_warehouse", "to_warehouse", "created_by")
            .all()
            .order_by("-created_at")
        )

        product_id = (request.GET.get("product") or "").strip()
        from_warehouse = (request.GET.get("from_warehouse") or "").strip()
        to_warehouse = (request.GET.get("to_warehouse") or "").strip()

        if product_id:
            queryset = queryset.filter(product_id=product_id)

        if from_warehouse:
            queryset = queryset.filter(from_warehouse_id=from_warehouse)

        if to_warehouse:
            queryset = queryset.filter(to_warehouse_id=to_warehouse)

        return Response([
            {
                "id": transfer.id,
                "product_id": transfer.product_id,
                "product_name": transfer.product.name if transfer.product else "",
                "product_sku": transfer.product.sku if transfer.product else "",
                "from_warehouse_id": transfer.from_warehouse_id,
                "from_warehouse_name": transfer.from_warehouse.name if transfer.from_warehouse else "",
                "to_warehouse_id": transfer.to_warehouse_id,
                "to_warehouse_name": transfer.to_warehouse.name if transfer.to_warehouse else "",
                "quantity": transfer.quantity,
                "created_by_id": transfer.created_by_id,
                "created_by_username": transfer.created_by.username if transfer.created_by else "",
                "created_at": transfer.created_at,
            }
            for transfer in queryset
        ])

    @transaction.atomic
    def post(self, request):
        product_id = request.data.get("product")
        from_warehouse_id = request.data.get("from_warehouse")
        to_warehouse_id = request.data.get("to_warehouse")
        quantity = int(request.data.get("quantity") or 0)

        if not product_id:
            return Response({"detail": "Product is required."}, status=400)
        if not from_warehouse_id:
            return Response({"detail": "From warehouse is required."}, status=400)
        if not to_warehouse_id:
            return Response({"detail": "To warehouse is required."}, status=400)
        if quantity <= 0:
            return Response({"detail": "Quantity must be greater than zero."}, status=400)
        if str(from_warehouse_id) == str(to_warehouse_id):
            return Response({"detail": "From warehouse and to warehouse cannot be the same."}, status=400)

        product = Product.objects.filter(id=product_id).first()
        if not product:
            return Response({"detail": "Product not found."}, status=404)

        from_warehouse = Warehouse.objects.filter(id=from_warehouse_id).first()
        if not from_warehouse:
            return Response({"detail": "From warehouse not found."}, status=404)

        to_warehouse = Warehouse.objects.filter(id=to_warehouse_id).first()
        if not to_warehouse:
            return Response({"detail": "To warehouse not found."}, status=404)

        from_stock = (
            Stock.objects.select_for_update()
            .filter(product=product, warehouse=from_warehouse)
            .first()
        )
        if not from_stock:
            return Response({"detail": "Source stock record not found."}, status=400)
        if from_stock.quantity < quantity:
            return Response(
                {"detail": f"Insufficient stock in {from_warehouse.name}. Available: {from_stock.quantity}."},
                status=400,
            )

        to_stock = (
            Stock.objects.select_for_update()
            .filter(product=product, warehouse=to_warehouse)
            .first()
        )
        if not to_stock:
            to_stock = Stock.objects.create(product=product, warehouse=to_warehouse, quantity=0)

        from_stock.quantity -= quantity
        from_stock.save(update_fields=["quantity", "updated_at"])

        to_stock.quantity += quantity
        to_stock.save(update_fields=["quantity", "updated_at"])

        transfer = StockTransfer.objects.create(
            product=product,
            from_warehouse=from_warehouse,
            to_warehouse=to_warehouse,
            quantity=quantity,
            created_by=request.user if request.user.is_authenticated else None,
        )

        create_audit_log(
            actor=request.user,
            action="stock_transfer_created",
            target_type="stock_transfer",
            target_id=transfer.id,
            description=f"Transferred {quantity} of {product.name} from {from_warehouse.name} to {to_warehouse.name}.",
            metadata={
                "stock_transfer_id": transfer.id,
                "product_id": product.id,
                "product_name": product.name,
                "from_warehouse_id": from_warehouse.id,
                "from_warehouse_name": from_warehouse.name,
                "to_warehouse_id": to_warehouse.id,
                "to_warehouse_name": to_warehouse.name,
                "quantity": quantity,
                "source": "inventory_api",
            },
        )

        return Response(
            {
                "detail": "Stock transferred successfully.",
                "transfer": {
                    "id": transfer.id,
                    "product_id": transfer.product_id,
                    "product_name": transfer.product.name if transfer.product else "",
                    "from_warehouse_id": transfer.from_warehouse_id,
                    "from_warehouse_name": transfer.from_warehouse.name if transfer.from_warehouse else "",
                    "to_warehouse_id": transfer.to_warehouse_id,
                    "to_warehouse_name": transfer.to_warehouse.name if transfer.to_warehouse else "",
                    "quantity": transfer.quantity,
                    "created_by_username": transfer.created_by.username if transfer.created_by else "",
                    "created_at": transfer.created_at,
                },
            },
            status=201,
        )


class PurchaseOrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = (
            PurchaseOrder.objects
            .select_related("supplier", "warehouse", "created_by")
            .prefetch_related("items__product")
            .all()
            .order_by("-created_at")
        )

        return Response([
            {
                "id": po.id,
                "po_number": po.po_number,
                "supplier_id": po.supplier_id,
                "supplier_name": po.supplier.name if po.supplier else "",
                "warehouse_id": po.warehouse_id,
                "warehouse_name": po.warehouse.name if po.warehouse else "",
                "status": po.status,
                "notes": po.notes,
                "created_by_username": po.created_by.username if po.created_by else "",
                "created_at": po.created_at,
                "total_amount": str(po.total_amount),
                "items": [
                    {
                        "id": item.id,
                        "product_id": item.product_id,
                        "product_name": item.product.name if item.product else "",
                        "product_sku": item.product.sku if item.product else "",
                        "quantity": item.quantity,
                        "unit_cost": str(item.unit_cost),
                        "line_total": str(item.line_total),
                    }
                    for item in po.items.all()
                ],
            }
            for po in queryset
        ])
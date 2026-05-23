from decimal import Decimal
from datetime import date

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.utils import create_audit_log
from apps.finance.models import SupplierInvoice
from .models import (
    Product,
    Warehouse,
    Stock,
    Supplier,
    PurchaseOrder,
    PurchaseOrderItem,
    GoodsReceivedNote,
    GoodsReceivedNoteItem,
    StockBatch,
    StockTransfer,
)


def parse_date(value):
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def serialize_product(product):
    return {
        "id": product.id,
        "name": product.name,
        "sku": product.sku,
        "barcode": product.barcode,
        "description": product.description,
        "cost_price": str(product.cost_price),
        "selling_price": str(product.selling_price),
        "reorder_level": product.reorder_level,
        "is_active": product.is_active,
        "tax_rate": getattr(product, "tax_rate_id", None),
        "tax_rate_name": product.tax_rate.name if getattr(product, "tax_rate", None) else "",
    }


def serialize_supplier(supplier):
    return {
        "id": supplier.id,
        "name": supplier.name,
        "contact_person": supplier.contact_person,
        "email": supplier.email,
        "phone": supplier.phone,
        "address": supplier.address,
        "is_active": supplier.is_active,
    }


def serialize_warehouse(warehouse):
    return {
        "id": warehouse.id,
        "name": warehouse.name,
        "code": warehouse.code,
        "location": warehouse.location,
        "is_active": warehouse.is_active,
    }


def serialize_stock(stock):
    return {
        "id": stock.id,
        "product_id": stock.product_id,
        "product_name": stock.product.name if stock.product else "",
        "product_sku": stock.product.sku if stock.product else "",
        "warehouse_id": stock.warehouse_id,
        "warehouse_name": stock.warehouse.name if stock.warehouse else "",
        "quantity": stock.quantity,
        "updated_at": stock.updated_at,
    }


def serialize_batch(batch):
    return {
        "id": batch.id,
        "product_id": batch.product_id,
        "product_name": batch.product.name if batch.product else "",
        "product_sku": batch.product.sku if batch.product else "",
        "warehouse_id": batch.warehouse_id,
        "warehouse_name": batch.warehouse.name if batch.warehouse else "",
        "grn_id": batch.grn_id,
        "batch_number": batch.batch_number,
        "received_date": batch.received_date,
        "expiry_date": batch.expiry_date,
        "quantity_received": batch.quantity_received,
        "quantity_available": batch.quantity_available,
        "unit_cost": str(batch.unit_cost),
        "status": batch.status,
        "created_at": batch.created_at,
    }


def serialize_invoice(invoice):
    if not invoice:
        return None

    return {
        "id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "supplier_id": invoice.supplier_id,
        "supplier_name": invoice.supplier.name if invoice.supplier else "",
        "purchase_order_id": invoice.purchase_order_id,
        "status": invoice.status,
        "invoice_date": invoice.invoice_date,
        "due_date": invoice.due_date,
        "total_amount": str(invoice.total_amount),
        "amount_paid": str(invoice.amount_paid),
        "balance_due": str(invoice.balance_due),
        "notes": invoice.notes,
        "created_at": invoice.created_at,
    }


def serialize_grn(grn):
    return {
        "id": grn.id,
        "grn_number": grn.grn_number,
        "purchase_order_id": grn.purchase_order_id,
        "purchase_order_number": grn.purchase_order.po_number if grn.purchase_order else "",
        "supplier_name": grn.purchase_order.supplier.name if grn.purchase_order and grn.purchase_order.supplier else "",
        "warehouse_name": grn.purchase_order.warehouse.name if grn.purchase_order and grn.purchase_order.warehouse else "",
        "notes": grn.notes,
        "created_by_username": grn.created_by.username if grn.created_by else "",
        "created_at": grn.created_at,
        "total_received_quantity": grn.total_received_quantity,
        "items": [
            {
                "id": item.id,
                "purchase_order_item_id": item.purchase_order_item_id,
                "product_id": item.product_id,
                "product_name": item.product.name if item.product else "",
                "product_sku": item.product.sku if item.product else "",
                "batch_number": item.batch_number,
                "expiry_date": item.expiry_date,
                "quantity_received": item.quantity_received,
                "unit_cost": str(item.unit_cost),
                "line_total": str(item.line_total),
            }
            for item in grn.items.all()
        ],
    }


def serialize_purchase_order(po):
    linked_invoice = po.finance_invoices.first() if hasattr(po, "finance_invoices") else None

    return {
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
        "ordered_quantity_total": po.ordered_quantity_total,
        "received_quantity_total": po.received_quantity_total,
        "pending_quantity_total": po.pending_quantity_total,
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product.name if item.product else "",
                "product_sku": item.product.sku if item.product else "",
                "quantity": item.quantity,
                "received_quantity": item.received_quantity,
                "pending_quantity": item.pending_quantity,
                "unit_cost": str(item.unit_cost),
                "line_total": str(item.line_total),
            }
            for item in po.items.all()
        ],
        "invoice": serialize_invoice(linked_invoice),
    }


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

        return Response([serialize_product(product) for product in queryset])


class WarehouseListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Warehouse.objects.all().order_by("name")
        return Response([serialize_warehouse(warehouse) for warehouse in queryset])


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

        return Response([serialize_supplier(supplier) for supplier in queryset])


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

        return Response([serialize_stock(stock) for stock in queryset])


class StockBatchListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        warehouse_id = (request.GET.get("warehouse") or "").strip()
        product_id = (request.GET.get("product") or "").strip()
        status_value = (request.GET.get("status") or "").strip()

        queryset = (
            StockBatch.objects
            .select_related("product", "warehouse", "grn")
            .all()
            .order_by("expiry_date", "created_at")
        )

        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)

        if product_id:
            queryset = queryset.filter(product_id=product_id)

        if status_value:
            queryset = queryset.filter(status=status_value)

        return Response([serialize_batch(batch) for batch in queryset])


class StockTransferListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = (
            StockTransfer.objects
            .select_related("product", "from_warehouse", "to_warehouse", "created_by")
            .all()
            .order_by("-created_at")
        )

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

        from_stock = Stock.objects.select_for_update().filter(product=product, warehouse=from_warehouse).first()
        if not from_stock:
            return Response({"detail": "Source stock record not found."}, status=400)
        if from_stock.quantity < quantity:
            return Response(
                {"detail": f"Insufficient stock in {from_warehouse.name}. Available: {from_stock.quantity}."},
                status=400,
            )

        to_stock = Stock.objects.select_for_update().filter(product=product, warehouse=to_warehouse).first()
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

        return Response({"detail": "Stock transferred successfully."}, status=201)


class PurchaseOrderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = (
            PurchaseOrder.objects
            .select_related("supplier", "warehouse", "created_by")
            .prefetch_related("items__product", "finance_invoices__supplier")
            .all()
            .order_by("-created_at")
        )
        return Response([serialize_purchase_order(po) for po in queryset])

    @transaction.atomic
    def post(self, request):
        supplier_id = request.data.get("supplier")
        warehouse_id = request.data.get("warehouse")
        notes = request.data.get("notes", "")
        items = request.data.get("items") or []

        if not supplier_id:
            return Response({"detail": "Supplier is required."}, status=400)
        if not warehouse_id:
            return Response({"detail": "Warehouse is required."}, status=400)
        if not isinstance(items, list) or not items:
            return Response({"detail": "At least one PO item is required."}, status=400)

        supplier = Supplier.objects.filter(id=supplier_id, is_active=True).first()
        if not supplier:
            return Response({"detail": "Supplier not found."}, status=404)

        warehouse = Warehouse.objects.filter(id=warehouse_id, is_active=True).first()
        if not warehouse:
            return Response({"detail": "Warehouse not found."}, status=404)

        po = PurchaseOrder.objects.create(
            po_number=f"PO-{timezone.now().strftime('%Y%m%d%H%M%S%f')}",
            supplier=supplier,
            warehouse=warehouse,
            status=PurchaseOrder.STATUS_SUBMITTED,
            notes=notes,
            created_by=request.user if request.user.is_authenticated else None,
        )

        created_count = 0
        for row in items:
            product_id = row.get("product")
            quantity = int(row.get("quantity") or 0)
            unit_cost = row.get("unit_cost") or 0

            if not product_id or quantity <= 0:
                continue

            product = Product.objects.filter(id=product_id).first()
            if not product:
                continue

            PurchaseOrderItem.objects.create(
                purchase_order=po,
                product=product,
                quantity=quantity,
                unit_cost=unit_cost,
            )
            created_count += 1

        if created_count == 0:
            po.delete()
            return Response({"detail": "No valid PO items were supplied."}, status=400)

        create_audit_log(
            actor=request.user,
            action="purchase_order_created",
            target_type="purchase_order",
            target_id=po.id,
            description=f"Created purchase order {po.po_number}.",
            metadata={
                "purchase_order_id": po.id,
                "po_number": po.po_number,
                "supplier_id": po.supplier_id,
                "supplier_name": po.supplier.name,
                "warehouse_id": po.warehouse_id,
                "warehouse_name": po.warehouse.name,
                "items_count": created_count,
                "source": "inventory_api",
            },
        )

        po = (
            PurchaseOrder.objects
            .select_related("supplier", "warehouse", "created_by")
            .prefetch_related("items__product", "finance_invoices__supplier")
            .get(id=po.id)
        )

        return Response(
            {
                "detail": "Purchase order created successfully.",
                "purchase_order": serialize_purchase_order(po),
            },
            status=201,
        )


class PurchaseOrderDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = PurchaseOrder.objects.select_related(
        "supplier",
        "warehouse",
        "created_by",
    ).prefetch_related(
        "items__product",
        "goods_received_notes__items__product",
        "goods_received_notes__created_by",
        "finance_invoices__supplier",
    )

    def retrieve(self, request, *args, **kwargs):
        po = self.get_object()
        data = serialize_purchase_order(po)
        data["grns"] = [
            serialize_grn(grn)
            for grn in po.goods_received_notes.all().order_by("-created_at")
        ]
        return Response(data)


class PurchaseOrderGenerateInvoiceView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        po = (
            PurchaseOrder.objects
            .select_related("supplier", "warehouse")
            .prefetch_related("items__product", "finance_invoices")
            .filter(id=pk)
            .first()
        )

        if not po:
            return Response({"detail": "Purchase order not found."}, status=404)

        existing_invoice = po.finance_invoices.first()
        if existing_invoice:
            return Response(
                {
                    "detail": "Supplier invoice already exists for this purchase order.",
                    "invoice": serialize_invoice(existing_invoice),
                },
                status=200,
            )

        total_amount = Decimal(str(po.total_amount or 0))
        invoice = SupplierInvoice.objects.create(
            supplier=po.supplier,
            purchase_order=po,
            invoice_number=f"INV-PO-{po.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            invoice_date=timezone.localdate(),
            due_date=timezone.localdate(),
            total_amount=total_amount,
            amount_paid=Decimal("0.00"),
            balance_due=total_amount,
            status=SupplierInvoice.STATUS_UNPAID,
            notes=f"Generated from purchase order {po.po_number}.",
        )

        create_audit_log(
            actor=request.user,
            action="supplier_invoice_created_from_po",
            target_type="supplier_invoice",
            target_id=invoice.id,
            description=f"Generated supplier invoice {invoice.invoice_number} from purchase order {po.po_number}.",
            metadata={
                "invoice_id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "purchase_order_id": po.id,
                "purchase_order_number": po.po_number,
                "supplier_id": po.supplier_id,
                "supplier_name": po.supplier.name if po.supplier else "",
                "total_amount": str(total_amount),
                "source": "inventory_api",
            },
        )

        return Response(
            {
                "detail": "Supplier invoice generated successfully.",
                "invoice": serialize_invoice(invoice),
            },
            status=201,
        )


class GoodsReceivedNoteListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        purchase_order_id = (request.GET.get("purchase_order") or "").strip()

        queryset = (
            GoodsReceivedNote.objects
            .select_related("purchase_order", "purchase_order__supplier", "purchase_order__warehouse", "created_by")
            .prefetch_related("items__product")
            .all()
            .order_by("-created_at")
        )

        if purchase_order_id:
            queryset = queryset.filter(purchase_order_id=purchase_order_id)

        return Response([serialize_grn(grn) for grn in queryset])

    @transaction.atomic
    def post(self, request):
        purchase_order_id = request.data.get("purchase_order")
        notes = request.data.get("notes", "")
        items = request.data.get("items") or []

        if not purchase_order_id:
            return Response({"detail": "Purchase order is required."}, status=400)
        if not isinstance(items, list) or not items:
            return Response({"detail": "At least one GRN item is required."}, status=400)

        po = (
            PurchaseOrder.objects
            .select_for_update()
            .select_related("supplier", "warehouse")
            .prefetch_related("items__product")
            .filter(id=purchase_order_id)
            .first()
        )

        if not po:
            return Response({"detail": "Purchase order not found."}, status=404)
        if po.status == PurchaseOrder.STATUS_CANCELLED:
            return Response({"detail": "Cancelled purchase orders cannot be received."}, status=400)

        valid_rows = [
            row for row in items
            if int(row.get("quantity_received") or 0) > 0 and row.get("purchase_order_item")
        ]
        if not valid_rows:
            return Response({"detail": "At least one received quantity must be greater than zero."}, status=400)

        grn = GoodsReceivedNote.objects.create(
            grn_number=f"GRN-{timezone.now().strftime('%Y%m%d%H%M%S%f')}",
            purchase_order=po,
            notes=notes,
            created_by=request.user if request.user.is_authenticated else None,
        )

        created_count = 0

        for row in valid_rows:
            po_item_id = row.get("purchase_order_item")
            quantity_received = int(row.get("quantity_received") or 0)
            batch_number = (row.get("batch_number") or "").strip()
            expiry_date = parse_date(row.get("expiry_date"))

            if not batch_number:
                transaction.set_rollback(True)
                return Response({"detail": "Batch number is required for each received line."}, status=400)

            po_item = (
                PurchaseOrderItem.objects
                .select_for_update()
                .select_related("product", "purchase_order")
                .filter(id=po_item_id, purchase_order=po)
                .first()
            )

            if not po_item:
                continue

            if quantity_received > po_item.pending_quantity:
                transaction.set_rollback(True)
                return Response(
                    {"detail": f"Received quantity for {po_item.product.name} exceeds pending quantity ({po_item.pending_quantity})."},
                    status=400,
                )

            stock = Stock.objects.select_for_update().filter(product=po_item.product, warehouse=po.warehouse).first()
            if not stock:
                stock = Stock.objects.create(product=po_item.product, warehouse=po.warehouse, quantity=0)

            stock.quantity += quantity_received
            stock.save(update_fields=["quantity", "updated_at"])

            po_item.received_quantity += quantity_received
            po_item.save(update_fields=["received_quantity"])

            grn_item = GoodsReceivedNoteItem.objects.create(
                grn=grn,
                purchase_order_item=po_item,
                product=po_item.product,
                batch_number=batch_number,
                expiry_date=expiry_date,
                quantity_received=quantity_received,
                unit_cost=po_item.unit_cost,
            )

            batch = StockBatch.objects.create(
                product=po_item.product,
                warehouse=po.warehouse,
                grn=grn,
                grn_item=grn_item,
                purchase_order_item=po_item,
                batch_number=batch_number,
                received_date=timezone.localdate(),
                expiry_date=expiry_date,
                quantity_received=quantity_received,
                quantity_available=quantity_received,
                unit_cost=po_item.unit_cost,
                status=StockBatch.STATUS_ACTIVE,
            )
            batch.refresh_status(save=True)

            created_count += 1

        if created_count == 0:
            grn.delete()
            return Response({"detail": "No valid GRN items were supplied."}, status=400)

        po.refresh_status_from_items(save=True)

        create_audit_log(
            actor=request.user,
            action="grn_created",
            target_type="goods_received_note",
            target_id=grn.id,
            description=f"Received goods for purchase order {po.po_number} under {grn.grn_number}.",
            metadata={
                "grn_id": grn.id,
                "grn_number": grn.grn_number,
                "purchase_order_id": po.id,
                "purchase_order_number": po.po_number,
                "received_items_count": created_count,
                "warehouse_id": po.warehouse_id,
                "warehouse_name": po.warehouse.name if po.warehouse else "",
                "source": "inventory_api",
            },
        )

        po = (
            PurchaseOrder.objects
            .select_related("supplier", "warehouse", "created_by")
            .prefetch_related(
                "items__product",
                "goods_received_notes__items__product",
                "goods_received_notes__created_by",
                "finance_invoices__supplier",
            )
            .get(id=po.id)
        )

        return Response(
            {
                "detail": "Goods received successfully.",
                "grn": serialize_grn(grn),
                "purchase_order": serialize_purchase_order(po),
                "purchase_order_status": po.status,
            },
            status=status.HTTP_201_CREATED,
        )
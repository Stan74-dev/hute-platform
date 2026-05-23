from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.utils import create_audit_log
from apps.inventory.models import Stock
from .models import Sale, SaleItem, Refund, RefundItem


def money(value):
    return str(Decimal(value or 0).quantize(Decimal("0.01")))


def serialize_refund_item(item):
    return {
        "id": item.id,
        "sale_item": item.sale_item_id,
        "product": item.product_id,
        "product_name": item.product.name if item.product else "",
        "product_sku": item.product.sku if item.product else "",
        "quantity": item.quantity,
        "unit_price": money(item.unit_price),
        "unit_cost": money(item.unit_cost),
        "tax_rate_percent": money(item.tax_rate_percent),
        "line_subtotal": money(item.line_subtotal),
        "tax_amount": money(item.tax_amount),
        "line_total": money(item.line_total),
        "line_profit_reversed": money(item.line_profit_reversed),
        "returned_to_stock": item.returned_to_stock,
    }


def serialize_refund(refund):
    return {
        "id": refund.id,
        "refund_number": refund.refund_number,
        "sale": refund.sale_id,
        "receipt_number": refund.sale.receipt_number if refund.sale else "",
        "cashier": refund.cashier_id,
        "cashier_username": refund.cashier.username if refund.cashier else "",
        "payment_method": refund.payment_method,
        "reason": refund.reason,
        "subtotal_amount": money(refund.subtotal_amount),
        "tax_amount": money(refund.tax_amount),
        "total_amount": money(refund.total_amount),
        "total_cost": money(refund.total_cost),
        "total_profit_reversed": money(refund.total_profit_reversed),
        "created_at": refund.created_at,
        "items": [serialize_refund_item(item) for item in refund.items.select_related("product", "sale_item").all()],
    }


class RefundListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        refunds = (
            Refund.objects
            .select_related("sale", "cashier")
            .prefetch_related("items__product", "items__sale_item")
            .all()
            .order_by("-created_at")
        )

        return Response([serialize_refund(refund) for refund in refunds])

    @transaction.atomic
    def post(self, request):
        sale_id = request.data.get("sale") or request.data.get("sale_id")
        reason = str(request.data.get("reason") or "")
        payment_method = request.data.get("payment_method") or Refund.REFUND_CASH
        returned_to_stock = bool(request.data.get("returned_to_stock", True))
        rows = request.data.get("items") or []

        if not sale_id:
            return Response({"detail": "Sale is required."}, status=400)

        if not isinstance(rows, list) or not rows:
            return Response({"detail": "At least one refund item is required."}, status=400)

        sale = (
            Sale.objects
            .select_related("warehouse")
            .prefetch_related("items__product")
            .filter(id=sale_id)
            .first()
        )

        if not sale:
            return Response({"detail": "Sale not found."}, status=404)

        refund = Refund.objects.create(
            sale=sale,
            refund_number=f"RFND-{timezone.now().strftime('%Y%m%d%H%M%S%f')}",
            cashier=request.user if request.user.is_authenticated else None,
            payment_method=payment_method,
            reason=reason,
        )

        subtotal_amount = Decimal("0.00")
        tax_amount = Decimal("0.00")
        total_amount = Decimal("0.00")
        total_cost = Decimal("0.00")
        total_profit_reversed = Decimal("0.00")

        for row in rows:
            sale_item_id = row.get("sale_item") or row.get("sale_item_id")
            quantity = int(row.get("quantity") or 0)

            if not sale_item_id or quantity <= 0:
                continue

            sale_item = (
                SaleItem.objects
                .select_related("product", "sale__warehouse")
                .filter(id=sale_item_id, sale=sale)
                .first()
            )

            if not sale_item:
                transaction.set_rollback(True)
                return Response({"detail": f"Sale item {sale_item_id} not found on this sale."}, status=404)

            already_refunded = (
                RefundItem.objects
                .filter(sale_item=sale_item)
                .aggregate(total=Sum("quantity"))["total"] or 0
            )

            refundable_quantity = int(sale_item.quantity or 0) - int(already_refunded or 0)

            if quantity > refundable_quantity:
                transaction.set_rollback(True)
                return Response(
                    {
                        "detail": (
                            f"Cannot refund {quantity} of {sale_item.product.name}. "
                            f"Refundable quantity is {refundable_quantity}."
                        )
                    },
                    status=400,
                )

            refund_item = RefundItem.objects.create(
                refund=refund,
                sale_item=sale_item,
                product=sale_item.product,
                quantity=quantity,
                unit_price=sale_item.unit_price,
                unit_cost=sale_item.unit_cost,
                tax_rate_percent=sale_item.tax_rate_percent,
                returned_to_stock=returned_to_stock,
            )

            if returned_to_stock:
                stock, _created = Stock.objects.select_for_update().get_or_create(
                    product=sale_item.product,
                    warehouse=sale.warehouse,
                    defaults={"quantity": 0},
                )
                stock.quantity = int(stock.quantity or 0) + quantity
                try:
                    stock.save(update_fields=["quantity", "updated_at"])
                except Exception:
                    stock.save(update_fields=["quantity"])

            subtotal_amount += Decimal(refund_item.line_subtotal or 0)
            tax_amount += Decimal(refund_item.tax_amount or 0)
            total_amount += Decimal(refund_item.line_total or 0)
            total_cost += Decimal(refund_item.unit_cost or 0) * Decimal(refund_item.quantity or 0)
            total_profit_reversed += Decimal(refund_item.line_profit_reversed or 0)

        if not refund.items.exists():
            refund.delete()
            return Response({"detail": "No valid refund items were supplied."}, status=400)

        refund.subtotal_amount = subtotal_amount
        refund.tax_amount = tax_amount
        refund.total_amount = total_amount
        refund.total_cost = total_cost
        refund.total_profit_reversed = total_profit_reversed
        refund.save(update_fields=[
            "subtotal_amount",
            "tax_amount",
            "total_amount",
            "total_cost",
            "total_profit_reversed",
        ])

        create_audit_log(
            actor=request.user,
            action="refund_created",
            target_type="refund",
            target_id=refund.id,
            description=f"Created refund {refund.refund_number} for sale {sale.receipt_number}.",
            metadata={
                "refund_id": refund.id,
                "refund_number": refund.refund_number,
                "sale_id": sale.id,
                "receipt_number": sale.receipt_number,
                "total_amount": money(refund.total_amount),
                "returned_to_stock": returned_to_stock,
                "source": "sales_refund_api",
            },
        )

        refund = (
            Refund.objects
            .select_related("sale", "cashier")
            .prefetch_related("items__product", "items__sale_item")
            .get(id=refund.id)
        )

        return Response(
            {
                "detail": "Refund completed successfully.",
                "refund": serialize_refund(refund),
            },
            status=201,
        )


class RefundDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, refund_id):
        refund = (
            Refund.objects
            .select_related("sale", "cashier")
            .prefetch_related("items__product", "items__sale_item")
            .filter(id=refund_id)
            .first()
        )

        if not refund:
            return Response({"detail": "Refund not found."}, status=404)

        return Response(serialize_refund(refund))
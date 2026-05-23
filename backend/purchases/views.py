from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Supplier, Purchase, PurchaseItem
from .serializers import SupplierSerializer, PurchaseSerializer, PurchaseItemSerializer

from products.models import Product
from companies.models import Company
from inventory.models import InventoryTransaction

from accounting.models import Account, JournalEntry, JournalLine


class SupplierViewSet(viewsets.ModelViewSet):

    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer


class PurchaseViewSet(viewsets.ModelViewSet):

    queryset = Purchase.objects.all()
    serializer_class = PurchaseSerializer


class PurchaseItemViewSet(viewsets.ModelViewSet):

    queryset = PurchaseItem.objects.all()
    serializer_class = PurchaseItemSerializer


@api_view(["POST"])
def create_purchase(request):

    company_id = request.data.get("company")
    supplier_id = request.data.get("supplier")
    items = request.data.get("items", [])
    total = request.data.get("total")

    company = Company.objects.get(id=company_id)

    purchase = Purchase.objects.create(
        company=company,
        supplier_id=supplier_id,
        total_amount=total
    )

    for item in items:

        product = Product.objects.get(id=item["product"])
        quantity = item["quantity"]
        cost = item["cost_price"]

        PurchaseItem.objects.create(
            purchase=purchase,
            product=product,
            quantity=quantity,
            cost_price=cost
        )

        # Increase stock
        product.stock_quantity += quantity
        product.save()

        InventoryTransaction.objects.create(
            company=company,
            product=product,
            transaction_type="purchase",
            quantity=quantity,
            reference=f"Purchase {purchase.id}"
        )

    # Accounting entry
    inventory_account = Account.objects.get(code="1200")
    cash_account = Account.objects.get(code="1000")

    journal = JournalEntry.objects.create(
        company=company,
        reference=f"Purchase {purchase.id}"
    )

    JournalLine.objects.create(
        journal=journal,
        account=inventory_account,
        debit=total,
        credit=0
    )

    JournalLine.objects.create(
        journal=journal,
        account=cash_account,
        debit=0,
        credit=total
    )

    return Response({
        "status": "success",
        "purchase_id": purchase.id
    })

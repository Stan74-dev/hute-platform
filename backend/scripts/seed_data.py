from django.contrib.auth.models import User
from apps.accounts.models import UserProfile
from apps.inventory.models import Warehouse, Product, Stock


def run():
    admin_user, created = User.objects.get_or_create(
        username="admin",
        defaults={
            "email": "admin@hute.local",
            "is_staff": True,
            "is_superuser": True,
            "first_name": "System",
            "last_name": "Admin",
        },
    )

    if created:
        admin_user.set_password("Admin123!")
        admin_user.save()
    else:
        changed = False
        if not admin_user.is_staff:
            admin_user.is_staff = True
            changed = True
        if not admin_user.is_superuser:
            admin_user.is_superuser = True
            changed = True
        if changed:
            admin_user.save(update_fields=["is_staff", "is_superuser"])

    profile, _ = UserProfile.objects.get_or_create(user=admin_user, defaults={"role": "admin"})
    if profile.role != "admin":
        profile.role = "admin"
        profile.save(update_fields=["role", "updated_at"])

    warehouse_1, _ = Warehouse.objects.get_or_create(
        name="Main Warehouse",
        code="MAIN",
        defaults={"location": "HQ"},
    )
    warehouse_2, _ = Warehouse.objects.get_or_create(
        name="Branch Warehouse",
        code="BR01",
        defaults={"location": "Branch 1"},
    )

    products = [
        {
            "sku": "PRD-001",
            "barcode": "100000001",
            "name": "Rice 10kg",
            "selling_price": 18.00,
            "cost_price": 13.50,
        },
        {
            "sku": "PRD-002",
            "barcode": "100000002",
            "name": "Cooking Oil 2L",
            "selling_price": 4.80,
            "cost_price": 3.20,
        },
        {
            "sku": "PRD-003",
            "barcode": "100000003",
            "name": "Sugar 2kg",
            "selling_price": 2.70,
            "cost_price": 1.90,
        },
    ]

    for item in products:
        product, _ = Product.objects.get_or_create(
            sku=item["sku"],
            defaults={
                "barcode": item["barcode"],
                "name": item["name"],
                "selling_price": item["selling_price"],
                "cost_price": item["cost_price"],
            },
        )

        if not product.barcode:
            product.barcode = item["barcode"]
            product.save(update_fields=["barcode"])

        Stock.objects.get_or_create(
            warehouse=warehouse_1,
            product=product,
            defaults={"quantity": 100, "reorder_level": 10},
        )
        Stock.objects.get_or_create(
            warehouse=warehouse_2,
            product=product,
            defaults={"quantity": 50, "reorder_level": 5},
        )
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from products.models import Product
from inventory.models import Warehouse, Stock


def run():
    print("Seeding database...")

    # =========================
    # CREATE WAREHOUSES
    # =========================
    w1, _ = Warehouse.objects.get_or_create(name="Main Warehouse")
    w2, _ = Warehouse.objects.get_or_create(name="Shop Floor")

    # =========================
    # CREATE PRODUCTS
    # =========================
    products = [
        {"name": "Bread", "cost": 0.50, "price": 1.00},
        {"name": "Milk", "cost": 0.70, "price": 1.20},
        {"name": "Sugar", "cost": 0.80, "price": 1.50},
        {"name": "Rice 1kg", "cost": 1.50, "price": 2.50},
        {"name": "Cooking Oil", "cost": 3.00, "price": 5.00},
        {"name": "Soap", "cost": 0.60, "price": 1.20},
    ]

    created_products = []

    for p in products:
        product, _ = Product.objects.get_or_create(
            name=p["name"],
            defaults={
                "cost_price": p["cost"],
                "selling_price": p["price"],
            }
        )
        created_products.append(product)

    # =========================
    # CREATE STOCK
    # =========================
    for product in created_products:
        Stock.objects.get_or_create(
            product=product,
            warehouse=w1,
            defaults={"quantity": 100}
        )

        Stock.objects.get_or_create(
            product=product,
            warehouse=w2,
            defaults={"quantity": 50}
        )

    print("✅ Done! Sample data loaded.")


if __name__ == "__main__":
    run()
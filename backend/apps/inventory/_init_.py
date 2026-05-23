from django.urls import path
from .views import warehouses, warehouse_products

urlpatterns = [
    path("warehouses/", warehouses),
    path("warehouse-products/<int:warehouse_id>/", warehouse_products),
]
from django.urls import path

from .views import (
    ProductListView,
    WarehouseListView,
    SupplierListView,
    StockListView,
    StockTransferListCreateView,
    PurchaseOrderListView,
    from .views import GoodsReceiveView

urlpatterns += [
    path("grn/", GoodsReceiveView.as_view()),
]
)

urlpatterns = [
    path("products/", ProductListView.as_view()),
    path("warehouses/", WarehouseListView.as_view()),
    path("suppliers/", SupplierListView.as_view()),
    path("stock/", StockListView.as_view()),
    path("transfers/", StockTransferListCreateView.as_view()),
    path("purchase-orders/", PurchaseOrderListView.as_view()),
]
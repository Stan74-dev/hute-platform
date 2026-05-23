from django.urls import path

from .views import (
    ProductListView,
    WarehouseListView,
    SupplierListView,
    StockListView,
    StockBatchListView,
    StockTransferListCreateView,
    PurchaseOrderListCreateView,
    PurchaseOrderDetailView,
    PurchaseOrderGenerateInvoiceView,
    GoodsReceivedNoteListCreateView,
)

urlpatterns = [
    path("products/", ProductListView.as_view()),
    path("warehouses/", WarehouseListView.as_view()),
    path("suppliers/", SupplierListView.as_view()),
    path("stock/", StockListView.as_view()),
    path("stock-batches/", StockBatchListView.as_view()),
    path("transfers/", StockTransferListCreateView.as_view()),
    path("purchase-orders/", PurchaseOrderListCreateView.as_view()),
    path("purchase-orders/<int:pk>/", PurchaseOrderDetailView.as_view()),
    path("purchase-orders/<int:pk>/generate-invoice/", PurchaseOrderGenerateInvoiceView.as_view()),
    path("grns/", GoodsReceivedNoteListCreateView.as_view()),
]
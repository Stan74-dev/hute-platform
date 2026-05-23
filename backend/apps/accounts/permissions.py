from rest_framework.permissions import BasePermission


def get_user_role(user):
    if not user or not user.is_authenticated:
        return None

    if getattr(user, "is_superuser", False):
        return "admin"

    try:
        groups = set(user.groups.values_list("name", flat=True))
    except Exception:
        groups = set()

    if "admin" in groups:
        return "admin"
    if "cashier" in groups:
        return "cashier"
    if "warehouse_staff" in groups:
        return "warehouse_staff"
    if "finance_user" in groups:
        return "finance_user"

    return None


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return get_user_role(request.user) == "admin"


class IsCashier(BasePermission):
    def has_permission(self, request, view):
        return get_user_role(request.user) in ["cashier", "admin"]


class IsWarehouse(BasePermission):
    def has_permission(self, request, view):
        return get_user_role(request.user) in ["warehouse_staff", "admin"]


class IsWarehouseStaff(BasePermission):
    def has_permission(self, request, view):
        return get_user_role(request.user) in ["warehouse_staff", "admin"]


class IsFinance(BasePermission):
    def has_permission(self, request, view):
        return get_user_role(request.user) in ["finance_user", "admin"]


class IsFinanceUser(BasePermission):
    def has_permission(self, request, view):
        return get_user_role(request.user) in ["finance_user", "admin"]


class IsCashierOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return get_user_role(request.user) in ["cashier", "admin"]


class IsWarehouseOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return get_user_role(request.user) in ["warehouse_staff", "admin"]


class IsFinanceOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return get_user_role(request.user) in ["finance_user", "admin"]
from django.contrib.auth.models import Group
from .models import AuditLog


ROLES = ['admin', 'cashier', 'warehouse_staff', 'finance_user']


def ensure_roles():
    for role in ROLES:
        Group.objects.get_or_create(name=role)


def get_user_roles(user):
    if not user or not user.is_authenticated:
        return []

    if user.is_superuser:
        return ['admin']

    return list(user.groups.values_list('name', flat=True))


def get_primary_role(user):
    roles = get_user_roles(user)

    for role in ROLES:
        if role in roles:
            return role

    return 'unassigned'


def set_user_role(user, role_name):
    ensure_roles()
    user.groups.clear()

    if role_name in ROLES:
        group = Group.objects.get(name=role_name)
        user.groups.add(group)


def create_audit_log(actor=None, action='', target_type='', target_id='', description='', metadata=None):
    if metadata is None:
        metadata = {}

    AuditLog.objects.create(
        actor=actor if getattr(actor, 'is_authenticated', False) else None,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        description=description,
        metadata=metadata,
    )
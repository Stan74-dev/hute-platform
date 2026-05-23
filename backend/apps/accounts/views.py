from decimal import Decimal

from django.contrib.auth import authenticate, get_user_model
from django.db.models import Q
from django.utils import timezone
from .views_anomaly import AnomalyDashboardView

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken

from .models import AuditLog, TerminalDevice
from .permissions import IsAdmin
from .utils import (
    get_primary_role,
    get_user_roles,
    set_user_role,
    create_audit_log,
    ensure_roles,
    ROLES,
)

User = get_user_model()


def serialize_terminal(device):
    return {
        'id': device.id,
        'terminal_id': device.terminal_id,
        'terminal_name': device.terminal_name,
        'preferred_print_mode': device.preferred_print_mode,
        'auto_print': device.auto_print,
        'is_active': device.is_active,
        'last_seen_user': getattr(device.last_seen_user, 'username', '') if device.last_seen_user else '',
        'last_seen_user_id': device.last_seen_user_id,
        'last_seen_at': device.last_seen_at,
        'created_at': device.created_at,
        'updated_at': device.updated_at,
    }


def money(value):
    if value is None:
        return "0.00"
    return str(value)


class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        username = (request.data.get('username') or '').strip()
        password = request.data.get('password') or ''

        if not username or not password:
            return Response(
                {'detail': 'Username and password are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=username, password=password)

        if user is None:
            return Response(
                {'detail': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {'detail': 'This user account is inactive.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)

        create_audit_log(
            actor=user,
            action='login',
            target_type='user',
            target_id=user.id,
            description=f'{user.username} logged in',
            metadata={'username': user.username},
        )

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'id': request.user.id,
            'username': request.user.username,
            'email': getattr(request.user, 'email', ''),
            'first_name': getattr(request.user, 'first_name', ''),
            'last_name': getattr(request.user, 'last_name', ''),
            'role': get_primary_role(request.user),
            'roles': get_user_roles(request.user),
            'is_superuser': request.user.is_superuser,
            'is_staff': request.user.is_staff,
        })


class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ensure_roles()

        query = request.GET.get('q', '').strip()
        users = User.objects.all().order_by('username')

        if query:
            users = users.filter(
                Q(username__icontains=query)
                | Q(email__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
            )

        data = []
        for user in users:
            data.append({
                'id': user.id,
                'username': user.username,
                'email': getattr(user, 'email', ''),
                'first_name': getattr(user, 'first_name', ''),
                'last_name': getattr(user, 'last_name', ''),
                'role': get_primary_role(user),
                'roles': get_user_roles(user),
                'is_superuser': user.is_superuser,
                'is_staff': user.is_staff,
                'is_active': user.is_active,
            })

        return Response(data)


class UserCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ensure_roles()

        username = (request.data.get('username') or '').strip()
        password = request.data.get('password') or ''
        email = (request.data.get('email') or '').strip()
        first_name = (request.data.get('first_name') or '').strip()
        last_name = (request.data.get('last_name') or '').strip()
        role = (request.data.get('role') or '').strip()

        if not username:
            return Response({'detail': 'Username is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if not password:
            return Response({'detail': 'Password is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if len(password) < 4:
            return Response({'detail': 'Password must be at least 4 characters.'}, status=status.HTTP_400_BAD_REQUEST)

        if role not in ROLES:
            return Response(
                {'detail': f'Role must be one of: {", ".join(ROLES)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(username=username).exists():
            return Response({'detail': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        if email and User.objects.filter(email=email).exists():
            return Response({'detail': 'Email already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
        )

        set_user_role(user, role)

        create_audit_log(
            actor=request.user,
            action='user_created',
            target_type='user',
            target_id=user.id,
            description=f'Created user {user.username} with role {role}',
            metadata={
                'username': user.username,
                'email': user.email,
                'role': role,
            },
        )

        return Response(
            {
                'detail': 'User created successfully.',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': get_primary_role(user),
                    'roles': get_user_roles(user),
                    'is_superuser': user.is_superuser,
                    'is_staff': user.is_staff,
                    'is_active': user.is_active,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class UserRoleUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        ensure_roles()

        role = (request.data.get('role') or '').strip()

        if role not in ROLES:
            return Response(
                {'detail': f'Role must be one of: {", ".join(ROLES)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        old_role = get_primary_role(user)
        set_user_role(user, role)

        create_audit_log(
            actor=request.user,
            action='role_update',
            target_type='user',
            target_id=user.id,
            description=f'{user.username}: {old_role} → {role}',
            metadata={
                'username': user.username,
                'old_role': old_role,
                'new_role': role,
            },
        )

        return Response({
            'detail': 'Role updated',
            'user': {
                'id': user.id,
                'username': user.username,
                'role': get_primary_role(user),
                'roles': get_user_roles(user),
            },
        })


class AuditLogListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logs = AuditLog.objects.select_related('actor').all()

        q = request.GET.get('q', '').strip()
        if q:
            logs = logs.filter(
                Q(action__icontains=q)
                | Q(description__icontains=q)
                | Q(target_type__icontains=q)
                | Q(target_id__icontains=q)
                | Q(actor__username__icontains=q)
            )

        logs = logs.order_by('-created_at')[:300]

        data = []
        for log in logs:
            data.append({
                'id': log.id,
                'actor': log.actor.username if log.actor else 'System',
                'action': log.action,
                'target_type': log.target_type,
                'target_id': log.target_id,
                'description': log.description,
                'metadata': log.metadata,
                'created_at': log.created_at,
            })

        return Response(data)


class TerminalRegisterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        terminal_id = (request.data.get('terminal_id') or '').strip()
        terminal_name = (request.data.get('terminal_name') or '').strip()
        preferred_print_mode = (request.data.get('preferred_print_mode') or 'browser').strip()
        auto_print = bool(request.data.get('auto_print', True))

        if not terminal_id:
            return Response({'detail': 'terminal_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if not terminal_name:
            return Response({'detail': 'terminal_name is required.'}, status=status.HTTP_400_BAD_REQUEST)

        existing = TerminalDevice.objects.filter(terminal_id=terminal_id).first()

        if existing and not existing.is_active:
            create_audit_log(
                actor=request.user,
                action='terminal_register_blocked',
                target_type='terminal',
                target_id=existing.id,
                description=f'Blocked inactive terminal {existing.terminal_name} from registering.',
                metadata={
                    'terminal_id': existing.terminal_id,
                    'terminal_name': existing.terminal_name,
                },
            )
            return Response(
                {
                    'detail': 'This terminal is inactive and cannot be used. Please contact an administrator.',
                    'terminal': serialize_terminal(existing),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        device, created = TerminalDevice.objects.get_or_create(
            terminal_id=terminal_id,
            defaults={
                'terminal_name': terminal_name,
                'preferred_print_mode': preferred_print_mode,
                'auto_print': auto_print,
                'last_seen_user': request.user,
                'last_seen_at': timezone.now(),
                'is_active': True,
            },
        )

        if not created:
            device.terminal_name = terminal_name
            device.preferred_print_mode = preferred_print_mode
            device.auto_print = auto_print
            device.last_seen_user = request.user
            device.last_seen_at = timezone.now()
            device.save()

        create_audit_log(
            actor=request.user,
            action='terminal_registered' if created else 'terminal_updated',
            target_type='terminal',
            target_id=device.id,
            description=f'{"Registered" if created else "Updated"} terminal {device.terminal_name}.',
            metadata={
                'terminal_id': device.terminal_id,
                'terminal_name': device.terminal_name,
                'preferred_print_mode': device.preferred_print_mode,
                'auto_print': device.auto_print,
            },
        )

        return Response(
            {
                'detail': 'Terminal saved successfully.',
                'terminal': serialize_terminal(device),
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class TerminalListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        q = (request.GET.get('q') or '').strip()

        queryset = TerminalDevice.objects.select_related('last_seen_user').all().order_by('terminal_name', 'terminal_id')

        if q:
            queryset = queryset.filter(
                Q(terminal_name__icontains=q)
                | Q(terminal_id__icontains=q)
                | Q(last_seen_user__username__icontains=q)
            )

        return Response([serialize_terminal(device) for device in queryset])


class TerminalDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, terminal_id):
        device = TerminalDevice.objects.filter(terminal_id=terminal_id).select_related('last_seen_user').first()
        if not device:
            return Response({'detail': 'Terminal not found.'}, status=status.HTTP_404_NOT_FOUND)

        return Response(serialize_terminal(device))


class TerminalUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, terminal_id):
        device = TerminalDevice.objects.filter(terminal_id=terminal_id).select_related('last_seen_user').first()
        if not device:
            return Response({'detail': 'Terminal not found.'}, status=status.HTTP_404_NOT_FOUND)

        old_state = {
            'terminal_name': device.terminal_name,
            'preferred_print_mode': device.preferred_print_mode,
            'auto_print': device.auto_print,
            'is_active': device.is_active,
        }

        terminal_name = request.data.get('terminal_name')
        preferred_print_mode = request.data.get('preferred_print_mode')
        auto_print = request.data.get('auto_print')
        is_active = request.data.get('is_active')

        if terminal_name is not None:
            device.terminal_name = str(terminal_name).strip() or device.terminal_name

        if preferred_print_mode is not None:
            device.preferred_print_mode = str(preferred_print_mode).strip() or device.preferred_print_mode

        if auto_print is not None:
            device.auto_print = bool(auto_print)

        if is_active is not None:
            device.is_active = bool(is_active)

        device.save()

        create_audit_log(
            actor=request.user,
            action='terminal_admin_updated',
            target_type='terminal',
            target_id=device.id,
            description=f'Admin updated terminal {device.terminal_name}.',
            metadata={
                'terminal_id': device.terminal_id,
                'old_state': old_state,
                'new_state': {
                    'terminal_name': device.terminal_name,
                    'preferred_print_mode': device.preferred_print_mode,
                    'auto_print': device.auto_print,
                    'is_active': device.is_active,
                },
            },
        )

        return Response({
            'detail': 'Terminal updated successfully.',
            'terminal': serialize_terminal(device),
        })


class TerminalActivityDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        terminals = list(
            TerminalDevice.objects.select_related('last_seen_user').all().order_by('terminal_name', 'terminal_id')
        )

        sales_logs = list(
            AuditLog.objects.filter(action='sale_checkout').select_related('actor').order_by('-created_at')
        )

        sales_by_terminal = {}
        total_sales_count = 0
        total_sales_amount = Decimal('0.00')

        for log in sales_logs:
            metadata = log.metadata or {}

            terminal_id = str(metadata.get('terminal_id') or '').strip()
            terminal_name = str(metadata.get('terminal_name') or '').strip()

            if not terminal_id:
                terminal_id = 'UNKNOWN'
            if not terminal_name:
                terminal_name = 'Unknown Terminal'

            amount = Decimal(str(metadata.get('total_amount', 0) or 0))

            key = terminal_id

            if key not in sales_by_terminal:
                sales_by_terminal[key] = {
                    'terminal_id': terminal_id,
                    'terminal_name': terminal_name,
                    'sales_count': 0,
                    'sales_amount': Decimal('0.00'),
                    'last_sale_at': log.created_at,
                }

            sales_by_terminal[key]['sales_count'] += 1
            sales_by_terminal[key]['sales_amount'] += amount

            if log.created_at > sales_by_terminal[key]['last_sale_at']:
                sales_by_terminal[key]['last_sale_at'] = log.created_at

            total_sales_count += 1
            total_sales_amount += amount

        terminal_records = []
        seen_terminal_ids = set()

        for terminal in terminals:
            matched = sales_by_terminal.get(terminal.terminal_id)

            terminal_records.append({
                'terminal_id': terminal.terminal_id,
                'terminal_name': terminal.terminal_name,
                'preferred_print_mode': terminal.preferred_print_mode,
                'auto_print': terminal.auto_print,
                'is_active': terminal.is_active,
                'last_seen_user': getattr(terminal.last_seen_user, 'username', '') if terminal.last_seen_user else '',
                'last_seen_at': terminal.last_seen_at,
                'sales_count': matched['sales_count'] if matched else 0,
                'sales_amount': money(matched['sales_amount']) if matched else '0.00',
                'last_sale_at': matched['last_sale_at'] if matched else None,
            })

            seen_terminal_ids.add(terminal.terminal_id)

        for terminal_id, agg in sales_by_terminal.items():
            if terminal_id in seen_terminal_ids:
                continue

            terminal_records.append({
                'terminal_id': agg['terminal_id'],
                'terminal_name': agg['terminal_name'],
                'preferred_print_mode': '',
                'auto_print': False,
                'is_active': False,
                'last_seen_user': '',
                'last_seen_at': None,
                'sales_count': agg['sales_count'],
                'sales_amount': money(agg['sales_amount']),
                'last_sale_at': agg['last_sale_at'],
            })

        terminal_records.sort(key=lambda row: (-int(row['sales_count']), row['terminal_name'] or ''))

        recent_activity = []
        for log in sales_logs[:100]:
            metadata = log.metadata or {}
            recent_activity.append({
                'id': log.id,
                'created_at': log.created_at,
                'actor': log.actor.username if log.actor else 'System',
                'terminal_id': str(metadata.get('terminal_id') or '').strip(),
                'terminal_name': str(metadata.get('terminal_name') or '').strip(),
                'receipt_number': str(metadata.get('receipt_number') or '').strip(),
                'warehouse_name': str(metadata.get('warehouse_name') or '').strip(),
                'total_amount': money(Decimal(str(metadata.get('total_amount', 0) or 0))),
            })

        return Response({
            'summary': {
                'registered_terminals': len(terminals),
                'active_terminals': len([t for t in terminals if t.is_active]),
                'inactive_terminals': len([t for t in terminals if not t.is_active]),
                'terminals_with_sales': len(sales_by_terminal),
                'total_sales_count': total_sales_count,
                'total_sales_amount': money(total_sales_amount),
            },
            'terminals': terminal_records,
            'recent_activity': recent_activity,
        })
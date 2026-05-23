from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        identity = (request.data.get("username") or request.data.get("email") or "").strip()
        password = request.data.get("password") or ""

        if not identity:
            return Response({"detail": "Username is required."}, status=400)

        if not password:
            return Response({"detail": "Password is required."}, status=400)

        user = None

        # Match by username first
        user = User.objects.filter(username__iexact=identity).first()

        # If not found, also allow email
        if user is None:
            user = User.objects.filter(email__iexact=identity).first()

        if user is None:
            return Response({"detail": "User not found."}, status=401)

        if not user.is_active:
            return Response({"detail": "User account is inactive."}, status=403)

        # Check password directly against stored hash
        if not user.check_password(password):
            return Response({"detail": "Invalid password."}, status=401)

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "username": user.get_username(),
                    "email": user.email,
                    "is_staff": user.is_staff,
                    "is_superuser": user.is_superuser,
                },
            },
            status=200,
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response(
            {
                "id": user.id,
                "username": user.get_username(),
                "email": user.email,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
            }
        )
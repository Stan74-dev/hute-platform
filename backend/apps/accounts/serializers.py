from django.contrib.auth.models import User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="profile.role", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_staff",
            "is_superuser",
            "role",
        ]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(
        choices=["admin", "manager", "cashier"],
        write_only=True,
        required=False,
        default="cashier",
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "password", "role"]

    def create(self, validated_data):
        role = validated_data.pop("role", "cashier")
        password = validated_data.pop("password")

        user = User.objects.create_user(password=password, **validated_data)

        if role == "admin":
            user.is_staff = True
            user.save(update_fields=["is_staff"])

        user.profile.role = role
        user.profile.save(update_fields=["role", "updated_at"])
        return user
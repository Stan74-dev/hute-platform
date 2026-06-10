from rest_framework import serializers
from .models import Branch, BranchTerminal

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = "__all__"
        read_only_fields = ["created_by", "created_at"]

class BranchTerminalSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = BranchTerminal
        fields = "__all__"

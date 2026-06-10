from rest_framework import viewsets, permissions
from .models import Branch, BranchTerminal
from .serializers import BranchSerializer, BranchTerminalSerializer

class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class BranchTerminalViewSet(viewsets.ModelViewSet):
    queryset = BranchTerminal.objects.select_related("branch").all()
    serializer_class = BranchTerminalSerializer
    permission_classes = [permissions.IsAuthenticated]

from django.utils import timezone

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models_anomaly import AnomalyScanRun


class AnomalyDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_str = (request.GET.get("date") or "").strip()

        if date_str:
            try:
                target_date = timezone.datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response({"detail": "Invalid date. Use YYYY-MM-DD."}, status=400)
        else:
            target_date = timezone.localdate()

        latest_scan = (
            AnomalyScanRun.objects
            .filter(scan_date=target_date, status="completed")
            .order_by("-completed_at", "-started_at")
            .first()
        )

        if not latest_scan:
            return Response({
                "date": str(target_date),
                "summary": {
                    "total_anomalies": 0,
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                    "auto_case_created_count": 0,
                    "auto_case_reused_count": 0,
                },
                "anomalies": [],
            })

        anomalies_qs = latest_scan.anomalies.select_related("case").all()

        anomalies = []
        for item in anomalies_qs.order_by("-score", "title")[:200]:
            anomalies.append({
                "id": item.id,
                "anomaly_type": item.anomaly_type,
                "type": item.anomaly_type,
                "severity": item.severity,
                "score": item.score,
                "title": item.title,
                "description": item.description,
                "case_id": item.case_id,
                "case_status": item.case.status if item.case else None,
                "created_at": item.created_at,
            })

        return Response({
            "date": str(target_date),
            "summary": {
                "total_anomalies": anomalies_qs.count(),
                "critical": anomalies_qs.filter(severity="critical").count(),
                "high": anomalies_qs.filter(severity="high").count(),
                "medium": anomalies_qs.filter(severity="medium").count(),
                "low": anomalies_qs.filter(severity="low").count(),
                "auto_case_created_count": latest_scan.auto_case_created_count or 0,
                "auto_case_reused_count": latest_scan.auto_case_reused_count or 0,
            },
            "anomalies": anomalies,
        })
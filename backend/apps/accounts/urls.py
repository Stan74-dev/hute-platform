from django.urls import path

from .views import (
    LoginView,
    MeView,
    UserListView,
    AuditLogListView,
)
from .views_shift import (
    StartShiftView,
    EndShiftView,
    CurrentShiftView,
    ShiftStatusView,
    LastClosedShiftView,
    ShiftListView,
    ShiftHistoryView,
    ShiftDetailView,
    DailySummaryView,
    ShiftSalesReportView,
    ShiftVarianceDashboardView,
    AllShiftsAdminView,
    HistoricalTrendsView,
    TerminalActivityView,
    ShiftAlertListView,
    ShiftAlertUnreadCountView,
    MarkShiftAlertsReadView,
    AnomalyCaseListCreateView,
    AnomalyCaseDetailView,
    AnomalyCaseEvidenceListCreateView,
    AnomalyCaseEvidenceDetailView,
    AnomalyCaseEvidenceDownloadView,
    ShiftReportPdfView,
    TerminalListView,
    TerminalRegisterView,
    AnomalyDashboardView,
)

urlpatterns = [
    path("login/", LoginView.as_view()),
    path("me/", MeView.as_view()),
    path("users/", UserListView.as_view()),
    path("audit-logs/", AuditLogListView.as_view()),

    path("shift/start/", StartShiftView.as_view()),
    path("shift/end/", EndShiftView.as_view()),
    path("shift/current/", CurrentShiftView.as_view()),
    path("shift/status/", ShiftStatusView.as_view()),
    path("shift/last-closed/", LastClosedShiftView.as_view()),
    path("shift/history/", ShiftHistoryView.as_view()),
    path("shift/detail/", ShiftDetailView.as_view()),
    path("shift/detail/<int:shift_id>/", ShiftDetailView.as_view()),
    path("shift/sales-report/", ShiftSalesReportView.as_view()),
    path("shift/variance-dashboard/", ShiftVarianceDashboardView.as_view()),
    path("shift/report-pdf/", ShiftReportPdfView.as_view()),

    path("daily-summary/", DailySummaryView.as_view()),
    path("historical-trends/", HistoricalTrendsView.as_view()),
    path("terminal-activity/", TerminalActivityView.as_view()),

    path("shifts/all/", AllShiftsAdminView.as_view()),
    path("shifts/", ShiftListView.as_view()),
    path("shift/list/", ShiftListView.as_view()),

    # aliases used by frontend
    path("shift-variance/", ShiftVarianceDashboardView.as_view()),
    path("anomaly-dashboard/", AnomalyDashboardView.as_view()),
    path("terminals/", TerminalListView.as_view()),
    path("terminals/register/", TerminalRegisterView.as_view()),

    path("shift-alerts/", ShiftAlertListView.as_view()),
    path("shift-alerts/unread-count/", ShiftAlertUnreadCountView.as_view()),
    path("shift-alerts/mark-read/", MarkShiftAlertsReadView.as_view()),

    path("anomaly-cases/", AnomalyCaseListCreateView.as_view()),
    path("anomaly-cases/<int:case_id>/", AnomalyCaseDetailView.as_view()),
    path("anomaly-cases/<int:case_id>/evidence/", AnomalyCaseEvidenceListCreateView.as_view()),
    path("anomaly-cases/<int:case_id>/evidence/<int:evidence_id>/", AnomalyCaseEvidenceDetailView.as_view()),
    path("anomaly-cases/<int:case_id>/evidence/<int:evidence_id>/download/", AnomalyCaseEvidenceDownloadView.as_view()),
]
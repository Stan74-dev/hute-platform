from io import BytesIO
from decimal import Decimal

from django.http import HttpResponse
from django.utils import timezone

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from apps.accounts.permissions import IsAdmin
from apps.accounts.models_case import AnomalyCase
from apps.accounts.models_shift import CashierShift
from apps.sales.models import Sale, SaleItem


styles = getSampleStyleSheet()


def money(value):
    if value is None:
        return "0.00"
    try:
        return f"{Decimal(str(value)):.2f}"
    except Exception:
        return "0.00"


def build_pdf_response(filename: str, pdf_bytes: bytes) -> HttpResponse:
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def render_pdf(elements) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def title(text: str):
    return Paragraph(f"<b>{text}</b>", styles["Title"])


def heading(text: str):
    return Paragraph(f"<b>{text}</b>", styles["Heading2"])


def body(text: str):
    return Paragraph(str(text), styles["BodyText"])


def spacer(height: int = 10):
    return Spacer(1, height)


def styled_table(data, col_widths=None):
    table = Table(data, colWidths=col_widths)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


class ExportCasePdfView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, case_id):
        case = (
            AnomalyCase.objects.select_related("assigned_to", "created_by")
            .filter(id=case_id)
            .first()
        )
        if not case:
            return Response({"detail": "Case not found."}, status=404)

        evidence_items = list(getattr(case, "evidence_items", []).all()) if hasattr(case, "evidence_items") else []
        timeline_items = list(getattr(case, "timeline", []).all()) if hasattr(case, "timeline") else []

        elements = [
            title(f"HUTE Anomaly Case Report #{case.id}"),
            spacer(),
            body(f"Generated: {timezone.now()}"),
            spacer(16),
            heading("Case Overview"),
            body(f"Title: {case.title or '-'}"),
            body(f"Description: {case.description or '-'}"),
            body(f"Anomaly Type: {getattr(case, 'anomaly_type', '-') or '-'}"),
            body(f"Severity: {getattr(case, 'severity', '-') or '-'}"),
            body(f"Score: {getattr(case, 'score', '-') or '-'}"),
            body(f"Status: {case.status or '-'}"),
            body(f"Priority: {case.priority or '-'}"),
            body(f"Assigned To: {getattr(case.assigned_to, 'username', '-') if case.assigned_to else '-'}"),
            body(f"Created By: {getattr(case.created_by, 'username', '-') if getattr(case, 'created_by', None) else '-'}"),
            body(f"Detected Date: {getattr(case, 'detected_date', '-') or '-'}"),
            body(f"SLA Due: {getattr(case, 'sla_due_at', '-') or '-'}"),
            body(f"SLA Breached: {'Yes' if getattr(case, 'sla_breached', False) else 'No'}"),
            body(f"Escalation Level: {getattr(case, 'escalation_level', 0)}"),
            spacer(16),
            heading("Notes"),
            body(getattr(case, "notes", "") or "-"),
            spacer(12),
            heading("Resolution Notes"),
            body(getattr(case, "resolution_notes", "") or "-"),
            spacer(16),
        ]

        evidence_table = [["Filename", "Note", "Uploaded By", "Created At"]]
        for ev in evidence_items:
            evidence_table.append([
                getattr(ev, "original_filename", "-") or "-",
                getattr(ev, "note", "-") or "-",
                getattr(getattr(ev, "uploaded_by", None), "username", "-") if getattr(ev, "uploaded_by", None) else "-",
                str(getattr(ev, "created_at", "-") or "-"),
            ])

        elements.append(heading("Evidence"))
        elements.append(
            styled_table(evidence_table, col_widths=[150, 170, 90, 110])
            if len(evidence_table) > 1
            else body("No evidence uploaded.")
        )
        elements.append(spacer(16))

        timeline_table = [["Action", "Description", "Performed By", "Created At"]]
        for item in timeline_items:
            timeline_table.append([
                getattr(item, "action", "-") or "-",
                getattr(item, "description", "-") or "-",
                getattr(getattr(item, "performed_by", None), "username", "System")
                if getattr(item, "performed_by", None)
                else "System",
                str(getattr(item, "created_at", "-") or "-"),
            ])

        elements.append(heading("Activity Timeline"))
        elements.append(
            styled_table(timeline_table, col_widths=[90, 220, 90, 110])
            if len(timeline_table) > 1
            else body("No activity recorded.")
        )

        pdf_bytes = render_pdf(elements)
        return build_pdf_response(f"case_{case.id}.pdf", pdf_bytes)


class ExportShiftPdfView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, shift_id):
        shift = (
            CashierShift.objects.select_related("user")
            .filter(id=shift_id)
            .first()
        )
        if not shift:
            return Response({"detail": "Shift not found."}, status=404)

        sales_qs = (
            Sale.objects.select_related("cashier", "warehouse")
            .filter(shift_id=shift.id)
            .order_by("-created_at")[:200]
        )

        total_sales_amount = Decimal("0.00")
        total_sales_profit = Decimal("0.00")
        cash_count = 0
        card_count = 0

        sales_table = [["Receipt", "Cashier", "Warehouse", "Payment", "Total", "Profit", "Created"]]
        for sale in sales_qs:
            total_sales_amount += Decimal(str(sale.total_amount or 0))
            total_sales_profit += Decimal(str(sale.total_profit or 0))

            if str(sale.payment_method or "").lower() == "cash":
                cash_count += 1
            else:
                card_count += 1

            sales_table.append([
                sale.receipt_number or "-",
                getattr(sale.cashier, "username", "-") if sale.cashier else "-",
                getattr(sale.warehouse, "name", "-") if sale.warehouse else "-",
                sale.payment_method or "-",
                money(sale.total_amount),
                money(sale.total_profit),
                str(sale.created_at or "-"),
            ])

        variance = Decimal(str(getattr(shift, "variance", 0) or 0))
        variance_status = "Balanced"
        if variance < 0:
            variance_status = "Short"
        elif variance > 0:
            variance_status = "Over"

        elements = [
            title(f"HUTE Shift Report #{shift.id}"),
            spacer(),
            body(f"Generated: {timezone.now()}"),
            spacer(16),
            heading("Shift Overview"),
            body(f"Cashier: {getattr(shift.user, 'username', '-') if shift.user else '-'}"),
            body(f"Terminal: {getattr(shift, 'terminal_id', '-') or '-'}"),
            body(f"Status: {getattr(shift, 'status', '-') or '-'}"),
            body(f"Opened At: {getattr(shift, 'opened_at', '-') or '-'}"),
            body(f"Closed At: {getattr(shift, 'closed_at', '-') or '-'}"),
            body(f"Opening Float: £{money(getattr(shift, 'opening_float', 0))}"),
            body(f"Cash Sales: £{money(getattr(shift, 'cash_sales', 0))}"),
            body(f"Card Sales: £{money(getattr(shift, 'card_sales', 0))}"),
            body(f"Expected Cash: £{money(getattr(shift, 'expected_cash', 0))}"),
            body(f"Actual Cash: £{money(getattr(shift, 'actual_cash', 0))}"),
            body(f"Variance: £{money(getattr(shift, 'variance', 0))}"),
            body(f"Variance Status: {variance_status}"),
            spacer(16),
            heading("Shift Summary"),
            body(f"Sales Count: {sales_qs.count()}"),
            body(f"Cash Sales Count: {cash_count}"),
            body(f"Card / Other Sales Count: {card_count}"),
            body(f"Total Sales Amount: £{money(total_sales_amount)}"),
            body(f"Total Sales Profit: £{money(total_sales_profit)}"),
            spacer(16),
            heading("Related Sales"),
            styled_table(sales_table, col_widths=[90, 70, 85, 60, 55, 55, 95])
            if len(sales_table) > 1
            else body("No related sales found."),
        ]

        pdf_bytes = render_pdf(elements)
        return build_pdf_response(f"shift_{shift.id}.pdf", pdf_bytes)


class ExportDayPdfView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        date_str = request.GET.get("date")
        if not date_str:
            return Response({"detail": "date is required. Use YYYY-MM-DD."}, status=400)

        try:
            target_date = timezone.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"detail": "Invalid date. Use YYYY-MM-DD."}, status=400)

        sales_qs = (
            Sale.objects.select_related("cashier", "warehouse")
            .filter(created_at__date=target_date)
            .order_by("-created_at")[:200]
        )

        shifts_qs = (
            CashierShift.objects.select_related("user")
            .filter(closed_at__date=target_date, status="closed")
            .order_by("-closed_at")[:100]
        )

        cases_qs = (
            AnomalyCase.objects.select_related("assigned_to")
            .filter(detected_date=target_date)
            .order_by("-created_at")[:100]
        )

        total_sales = Decimal("0.00")
        total_profit = Decimal("0.00")

        sales_table = [["Receipt", "Cashier", "Warehouse", "Payment", "Total", "Profit", "Created"]]
        for sale in sales_qs:
            total_sales += Decimal(str(sale.total_amount or 0))
            total_profit += Decimal(str(sale.total_profit or 0))
            sales_table.append([
                sale.receipt_number or "-",
                getattr(sale.cashier, "username", "-") if sale.cashier else "-",
                getattr(sale.warehouse, "name", "-") if sale.warehouse else "-",
                sale.payment_method or "-",
                money(sale.total_amount),
                money(sale.total_profit),
                str(sale.created_at or "-"),
            ])

        shifts_table = [["Shift ID", "Cashier", "Terminal", "Expected", "Actual", "Variance", "Closed"]]
        for shift in shifts_qs:
            shifts_table.append([
                str(shift.id),
                getattr(shift.user, "username", "-") if shift.user else "-",
                getattr(shift, "terminal_id", "-") or "-",
                money(getattr(shift, "expected_cash", 0)),
                money(getattr(shift, "actual_cash", 0)),
                money(getattr(shift, "variance", 0)),
                str(getattr(shift, "closed_at", "-") or "-"),
            ])

        cases_table = [["Case ID", "Title", "Status", "Priority", "Assigned", "SLA", "Esc."]]
        for case in cases_qs:
            cases_table.append([
                str(case.id),
                getattr(case, "title", "-") or "-",
                getattr(case, "status", "-") or "-",
                getattr(case, "priority", "-") or "-",
                getattr(case.assigned_to, "username", "-") if case.assigned_to else "-",
                "Breached" if getattr(case, "sla_breached", False) else "Healthy",
                str(getattr(case, "escalation_level", 0)),
            ])

        elements = [
            title(f"HUTE Day Investigation Report {target_date}"),
            spacer(),
            body(f"Generated: {timezone.now()}"),
            spacer(16),
            heading("Summary"),
            body(f"Sales Count: {sales_qs.count()}"),
            body(f"Shifts Count: {shifts_qs.count()}"),
            body(f"Cases Count: {cases_qs.count()}"),
            body(f"Total Sales: £{money(total_sales)}"),
            body(f"Total Profit: £{money(total_profit)}"),
            spacer(16),
            heading("Sales"),
            styled_table(sales_table, col_widths=[90, 70, 85, 60, 55, 55, 95])
            if len(sales_table) > 1
            else body("No sales found."),
            spacer(16),
            heading("Shifts"),
            styled_table(shifts_table, col_widths=[50, 75, 75, 60, 60, 60, 100])
            if len(shifts_table) > 1
            else body("No closed shifts found."),
            spacer(16),
            heading("Cases"),
            styled_table(cases_table, col_widths=[45, 170, 60, 55, 70, 50, 35])
            if len(cases_table) > 1
            else body("No cases found."),
        ]

        pdf_bytes = render_pdf(elements)
        return build_pdf_response(f"day_{target_date}.pdf", pdf_bytes)


class ExportSalePdfView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, sale_id):
        sale = (
            Sale.objects.select_related("cashier", "warehouse", "shift")
            .filter(id=sale_id)
            .first()
        )
        if not sale:
            return Response({"detail": "Sale not found."}, status=404)

        items_qs = (
            SaleItem.objects.select_related("product")
            .filter(sale_id=sale.id)
            .order_by("id")
        )

        item_count = 0
        total_quantity = 0
        items_table = [["Product", "SKU", "Qty", "Unit Price", "Line Total", "Line Profit"]]

        for item in items_qs:
            qty = int(getattr(item, "quantity", 0) or 0)
            item_count += 1
            total_quantity += qty
            items_table.append([
                getattr(getattr(item, "product", None), "name", "-") if getattr(item, "product", None) else "-",
                getattr(getattr(item, "product", None), "sku", "-") if getattr(item, "product", None) else "-",
                str(qty),
                money(getattr(item, "unit_price", 0)),
                money(getattr(item, "line_total", 0)),
                money(getattr(item, "line_profit", 0)),
            ])

        elements = [
            title(f"HUTE Sale Receipt Report #{sale.id}"),
            spacer(),
            body(f"Generated: {timezone.now()}"),
            spacer(16),
            heading("Sale Overview"),
            body(f"Receipt Number: {getattr(sale, 'receipt_number', '-') or '-'}"),
            body(f"Cashier: {getattr(sale.cashier, 'username', '-') if sale.cashier else '-'}"),
            body(f"Warehouse: {getattr(sale.warehouse, 'name', '-') if sale.warehouse else '-'}"),
            body(f"Shift ID: {getattr(sale, 'shift_id', '-') or '-'}"),
            body(f"Payment Method: {getattr(sale, 'payment_method', '-') or '-'}"),
            body(f"Total Amount: £{money(getattr(sale, 'total_amount', 0))}"),
            body(f"Total Cost: £{money(getattr(sale, 'total_cost', 0))}"),
            body(f"Total Profit: £{money(getattr(sale, 'total_profit', 0))}"),
            body(f"Created At: {getattr(sale, 'created_at', '-') or '-'}"),
            spacer(16),
            heading("Receipt Summary"),
            body(f"Item Lines: {item_count}"),
            body(f"Total Quantity: {total_quantity}"),
            spacer(16),
            heading("Receipt Items"),
            styled_table(items_table, col_widths=[160, 70, 35, 65, 65, 70])
            if len(items_table) > 1
            else body("No sale items found."),
        ]

        pdf_bytes = render_pdf(elements)
        return build_pdf_response(f"sale_{sale.id}.pdf", pdf_bytes)
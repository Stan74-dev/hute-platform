from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail


CRITICAL_VARIANCE_THRESHOLD = Decimal("100.00")


def get_shift_alert_severity(variance_abs):
    variance_abs = Decimal(str(variance_abs or 0))

    if variance_abs >= Decimal("100.00"):
        return "critical"
    if variance_abs >= Decimal("50.00"):
        return "high"
    if variance_abs >= Decimal("20.00"):
        return "medium"
    return "low"


def should_send_critical_variance_email(variance_abs):
    variance_abs = Decimal(str(variance_abs or 0))
    return variance_abs >= CRITICAL_VARIANCE_THRESHOLD


def send_critical_shift_variance_email(shift):
    recipients = getattr(settings, "SHIFT_ALERT_EMAIL_RECIPIENTS", [])
    if not recipients:
        return {
            "sent": False,
            "reason": "No SHIFT_ALERT_EMAIL_RECIPIENTS configured.",
        }

    variance = Decimal(str(getattr(shift, "variance", 0) or 0))
    variance_abs = abs(variance)

    if not should_send_critical_variance_email(variance_abs):
        return {
            "sent": False,
            "reason": "Variance does not meet critical threshold.",
        }

    cashier_username = getattr(getattr(shift, "user", None), "username", "Unknown")
    terminal_id = getattr(shift, "terminal_id", "UNKNOWN")

    if variance < 0:
        variance_type = "SHORT"
    elif variance > 0:
        variance_type = "OVER"
    else:
        variance_type = "BALANCED"

    subject = f"HUTE Critical Shift Variance Alert - Shift #{shift.id}"

    message = (
        f"Critical cash variance detected in HUTE.\n\n"
        f"Shift ID: {shift.id}\n"
        f"Cashier: {cashier_username}\n"
        f"Terminal ID: {terminal_id}\n"
        f"Opened At: {shift.opened_at}\n"
        f"Closed At: {shift.closed_at}\n"
        f"Opening Float: £{shift.opening_float}\n"
        f"Cash Sales: £{shift.cash_sales}\n"
        f"Card Sales: £{shift.card_sales}\n"
        f"Expected Cash: £{shift.expected_cash}\n"
        f"Actual Cash: £{shift.actual_cash}\n"
        f"Variance: £{shift.variance}\n"
        f"Variance Type: {variance_type}\n"
        f"Severity: {get_shift_alert_severity(variance_abs).upper()}\n"
    )

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
    if not from_email:
        from_email = "hute-alerts@localhost"

    send_mail(
        subject=subject,
        message=message,
        from_email=from_email,
        recipient_list=recipients,
        fail_silently=False,
    )

    return {
        "sent": True,
        "recipients": recipients,
        "subject": subject,
    }
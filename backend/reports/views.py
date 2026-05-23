from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum

from accounting.models import Account, JournalLine


@api_view(["GET"])
def profit_loss(request):

    revenue_accounts = Account.objects.filter(account_type="revenue")
    expense_accounts = Account.objects.filter(account_type="expense")

    revenue_total = (
        JournalLine.objects.filter(account__in=revenue_accounts)
        .aggregate(total=Sum("credit"))["total"] or 0
    )

    expense_total = (
        JournalLine.objects.filter(account__in=expense_accounts)
        .aggregate(total=Sum("debit"))["total"] or 0
    )

    profit = revenue_total - expense_total

    return Response({
        "revenue": revenue_total,
        "expenses": expense_total,
        "profit": profit
    })


@api_view(["GET"])
def balance_sheet(request):

    asset_accounts = Account.objects.filter(account_type="asset")
    liability_accounts = Account.objects.filter(account_type="liability")
    equity_accounts = Account.objects.filter(account_type="equity")

    assets = (
        JournalLine.objects.filter(account__in=asset_accounts)
        .aggregate(debit=Sum("debit"), credit=Sum("credit"))
    )

    liabilities = (
        JournalLine.objects.filter(account__in=liability_accounts)
        .aggregate(debit=Sum("debit"), credit=Sum("credit"))
    )

    equity = (
        JournalLine.objects.filter(account__in=equity_accounts)
        .aggregate(debit=Sum("debit"), credit=Sum("credit"))
    )

    asset_total = (assets["debit"] or 0) - (assets["credit"] or 0)
    liability_total = (liabilities["credit"] or 0) - (liabilities["debit"] or 0)
    equity_total = (equity["credit"] or 0) - (equity["debit"] or 0)

    return Response({

        "assets": asset_total,
        "liabilities": liability_total,
        "equity": equity_total,

        "check": asset_total == (liability_total + equity_total)

    })


@api_view(["GET"])
def general_ledger(request):

    accounts = Account.objects.all()

    ledger = []

    for account in accounts:

        lines = JournalLine.objects.filter(account=account).order_by("id")

        balance = 0
        transactions = []

        for line in lines:

            balance += (line.debit or 0)
            balance -= (line.credit or 0)

            transactions.append({

                "journal": line.journal.reference,
                "debit": line.debit,
                "credit": line.credit,
                "balance": balance

            })

        ledger.append({

            "account": account.name,
            "code": account.code,
            "transactions": transactions,
            "final_balance": balance

        })

    return Response(ledger)

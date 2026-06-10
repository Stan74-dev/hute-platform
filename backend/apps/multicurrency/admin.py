from django.contrib import admin
from .models import Currency, ExchangeRate, SplitTender, SplitTenderLine
admin.site.register(Currency)
admin.site.register(ExchangeRate)
admin.site.register(SplitTender)
admin.site.register(SplitTenderLine)

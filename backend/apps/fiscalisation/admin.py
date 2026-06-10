from django.contrib import admin
from .models import FiscalDevice, FiscalInvoice, FiscalSubmissionLog
admin.site.register(FiscalDevice)
admin.site.register(FiscalInvoice)
admin.site.register(FiscalSubmissionLog)

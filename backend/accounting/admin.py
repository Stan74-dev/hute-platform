from django.contrib import admin
from .models import Account, JournalEntry, JournalLine


admin.site.register(Account)
admin.site.register(JournalEntry)
admin.site.register(JournalLine)

from django.contrib import admin
from .models import SubscriptionPlan,Tenant,Subscription,LicenseKey
admin.site.register(SubscriptionPlan)
admin.site.register(Tenant)
admin.site.register(Subscription)
admin.site.register(LicenseKey)

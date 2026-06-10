from django.db import models
from django.utils import timezone
class SubscriptionPlan(models.Model):
    name=models.CharField(max_length=80,unique=True); monthly_price=models.DecimalField(max_digits=10,decimal_places=2,default=0)
    max_branches=models.PositiveIntegerField(default=1); max_users=models.PositiveIntegerField(default=2); max_terminals=models.PositiveIntegerField(default=1)
    has_fiscalisation=models.BooleanField(default=False); has_mobile_money=models.BooleanField(default=False); has_multicurrency=models.BooleanField(default=False); is_active=models.BooleanField(default=True)
    def __str__(self): return self.name
class Tenant(models.Model):
    business_name=models.CharField(max_length=160); trading_name=models.CharField(max_length=160,blank=True); tax_number=models.CharField(max_length=80,blank=True); contact_email=models.EmailField(blank=True); contact_phone=models.CharField(max_length=40,blank=True); is_active=models.BooleanField(default=True); created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.business_name
class Subscription(models.Model):
    tenant=models.ForeignKey(Tenant,on_delete=models.CASCADE,related_name="subscriptions"); plan=models.ForeignKey(SubscriptionPlan,on_delete=models.PROTECT); starts_at=models.DateField(default=timezone.localdate); ends_at=models.DateField(); is_active=models.BooleanField(default=True); payment_reference=models.CharField(max_length=120,blank=True)
    @property
    def is_valid(self): return self.is_active and self.ends_at >= timezone.localdate()
class LicenseKey(models.Model):
    tenant=models.ForeignKey(Tenant,on_delete=models.CASCADE,related_name="license_keys"); key=models.CharField(max_length=120,unique=True); is_active=models.BooleanField(default=True); activated_at=models.DateTimeField(null=True,blank=True); expires_at=models.DateField(null=True,blank=True)

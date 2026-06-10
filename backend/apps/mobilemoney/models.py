from django.conf import settings
from django.db import models
class MobileMoneyRequest(models.Model):
    PROVIDERS=[("ecocash","EcoCash"),("innbucks","InnBucks"),("mukuru","Mukuru"),("zipit","ZIPIT")]
    STATUSES=[("pending","Pending"),("customer_prompted","Customer Prompted"),("paid","Paid"),("failed","Failed"),("cancelled","Cancelled")]
    provider=models.CharField(max_length=30,choices=PROVIDERS)
    status=models.CharField(max_length=30,choices=STATUSES,default="pending")
    sale=models.ForeignKey("sales.Sale",null=True,blank=True,on_delete=models.SET_NULL,related_name="mobile_money_requests")
    amount=models.DecimalField(max_digits=14,decimal_places=2)
    currency=models.CharField(max_length=10,default="USD")
    customer_phone=models.CharField(max_length=40)
    internal_reference=models.CharField(max_length=120,unique=True)
    provider_reference=models.CharField(max_length=160,blank=True)
    request_payload=models.JSONField(default=dict,blank=True)
    response_payload=models.JSONField(default=dict,blank=True)
    callback_payload=models.JSONField(default=dict,blank=True)
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

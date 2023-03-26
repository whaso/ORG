from django.db import models
from orders.models import OrderInfo

class PayModel(models.Model):
    out_trade_no = models.ForeignKey(OrderInfo,on_delete=models.CASCADE,verbose_name="美多商城订单编号")
    trade_no = models.CharField(max_length=100,unique=True,null=True,blank=True,verbose_name="支付宝订单号")

    class Meta:
        db_table = "tb_payment"

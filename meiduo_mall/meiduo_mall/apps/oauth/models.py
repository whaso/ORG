from django.db import models
# from users.models import User
from meiduo_mall.utils.my_model import BaseModel

#1,美多qq用户模型类
class OAuthQQUser(BaseModel):
    user = models.ForeignKey("users.User",on_delete=models.CASCADE,verbose_name="美多用户")
    open_id = models.CharField(max_length=64,unique=True,verbose_name="qq用户id")

    class Meta:
        db_table = "tb_qq_users"

class SinaUser(BaseModel):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='梅朵用户')
    uid = models.CharField(max_length=64, unique=True, verbose_name="微博用户id")

    class Meta:
        db_table = 'tb_sina_users'
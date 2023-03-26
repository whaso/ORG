from django.db import models

#1,省市区
class Area(models.Model):
    name = models.CharField(max_length=20,verbose_name="区域名")
    parent = models.ForeignKey('self',related_name="subs",on_delete=models.SET_NULL,null=True,blank=True,verbose_name="父级区域")

    class Meta:
        db_table = "tb_areas"

    #为了方便查看对象的输出,重写__str__方法
    def __str__(self):
        # return "%s-%s".format(self.id,self.name)
        return self.name
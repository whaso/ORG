from django.shortcuts import render
from django.views import View
from goods.models import GoodsChannel
from .models import ContentCategory,Content
from meiduo_mall.utils.my_category import get_categories

#1,展示首页
class IndexView(View):
    def get(self,request):

        #1,获取分类数据
        categories = get_categories()

        #4,查询广告分类数据
        contents = {}
        content_category = ContentCategory.objects.order_by("id")
        for category in content_category:
            contents[category.key] = category.content_set.all()
            # contents[category.key] = Content.objects.filter(category_id=category1.id).all()

        #4,组装数据
        context = {
            "categories":categories,
            "contents":contents
        }

        #5,返回响应
        return render(request,'index.html',context=context)

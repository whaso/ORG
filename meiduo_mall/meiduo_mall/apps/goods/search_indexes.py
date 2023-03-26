import datetime
from haystack import indexes
from .models import SKU

class SKUIndex(indexes.SearchIndex, indexes.Indexable):
    #设置text数据的组成格式, 来自于模板在templates下面
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return SKU

    def index_queryset(self, using=None):
        "Used when the entire index for model is updated."
        return self.get_model().objects.filter(is_launched=True)
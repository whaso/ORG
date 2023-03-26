from rest_framework.generics import ListAPIView

from goods.models import SKU
from meiduo_admin.good import sku_images_serializers


class SKUSimpleView(ListAPIView):
    serializer_class = sku_images_serializers.SKUSimpleSerializer
    queryset = SKU.objects.order_by("id").all()
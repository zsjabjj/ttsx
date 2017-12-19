from django.contrib import admin

# Register your models here.
from goods.models import Goods, GoodsCategory, GoodsSKU, IndexPromotionBanner

admin.site.register(Goods)
admin.site.register(GoodsSKU)
admin.site.register(GoodsCategory)
admin.site.register(IndexPromotionBanner)
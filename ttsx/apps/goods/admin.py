from django.contrib import admin

# Register your models here.
from django.core.cache import cache

from goods.models import Goods, GoodsCategory, GoodsSKU, IndexPromotionBanner, IndexCategoryGoodsBanner
from Celery.tasks import get_static_index

class BaseAdmin(admin.ModelAdmin):
    """商品活动信息的管理类,运营人员在后台发布内容时，异步生成静态页面"""


    def save_model(self, request, obj, form, change):
        """后台保存对象数据时使用"""

        # obj是将站点管理操作的结果封装成对象
        # obj表示要保存的对象，调用save(),将对象保存到数据库中
        obj.save()
        # 调用celery异步生成静态文件方法，操作完表单后删除静态文件
        get_static_index.delay()
        # 修改了数据库数据就需要删除缓存,如果不删除,就还会是访问的旧数据
        cache.delete('index_page_data')

    def delete_model(self, request, obj):
        """后台删除对象数据时使用"""
        obj.delete()
        get_static_index.delay()
        cache.delete('index_page_data')

class IndexPromotionBannerAdmin(BaseAdmin):
    """商品活动站点管理，如果有自己的新的逻辑也是写在这里"""
    # list_display = []
    pass

class GoodsCategoryAdmin(BaseAdmin):
    pass

class GoodsAdmin(BaseAdmin):
    pass

class GoodsSKUAdmin(BaseAdmin):
    pass

class IndexCategoryGoodsBannerAdmin(BaseAdmin):
    pass


admin.site.register(Goods, GoodsAdmin)
admin.site.register(GoodsSKU, GoodsSKUAdmin)
admin.site.register(GoodsCategory, GoodsCategoryAdmin)
admin.site.register(IndexPromotionBanner, IndexPromotionBannerAdmin)
admin.site.register(IndexCategoryGoodsBanner, IndexCategoryGoodsBannerAdmin)
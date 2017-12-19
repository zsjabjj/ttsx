from django.shortcuts import render

# Create your views here.
from django.views.generic import View

# def index(request):
#     return render(request, 'index.html')
# 商品类别
from goods.models import GoodsCategory
# 商品轮播
from goods.models import IndexGoodsBanner
# 商品分类
from goods.models import IndexCategoryGoodsBanner
# 商品促销活动
from goods.models import IndexPromotionBanner


class IndexView(View):
    def get(self, request):
        '''主页查询数据'''
        # 查询商品类别信息
        categorys = GoodsCategory.objects.all()
        # 查询商品轮播,幻灯片
        banners = IndexGoodsBanner.objects.all().order_by('index')
        # 查询促销活动
        pbanners = IndexPromotionBanner.objects.all().order_by('index')
        # 查询分类商品
        for category in categorys:
            # 过滤出标题
            title = IndexCategoryGoodsBanner.objects.filter(category=category, display_type=0).order_by('index')
            category.title = title
            # 过滤出图片
            img = IndexCategoryGoodsBanner.objects.filter(category=category, display_type=1).order_by('index')
            category.img = img
        # 购物车数量
        cart_num = 0
        # 上下文数据
        context = {
            'categorys': categorys,
            'banners': banners,
            'pbanners': pbanners,
            'cart_num': cart_num
        }

        return render(request, 'index.html', context)

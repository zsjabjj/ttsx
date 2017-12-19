from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect

# Create your views here.
from django.views.generic import View

# def index(request):
#     return render(request, 'index.html')
# 商品类别
from django_redis import get_redis_connection

from goods.models import GoodsCategory
# 商品轮播
from goods.models import IndexGoodsBanner
# 商品分类
from goods.models import IndexCategoryGoodsBanner
# 商品促销活动
from goods.models import IndexPromotionBanner

# 详情页
from apps.goods.models import GoodsSKU


class DetailView(View):
    '''
    提示：
        检查是否有缓存，如果缓存不存在就查询数据；反之，直接读取缓存数据
        在商品详情页需要实现存储浏览记录的逻辑
        浏览记录存储在redis中，之前已经在用户中心界面实现了浏览记录的读取
    URL的设计：/detail/1
    '''
    # sku_id 获取的是点击的商品的id
    def get(self, request, sku_id):
        user = request.user
        # 获取缓存
        context = cache.get('detail_%s' % sku_id)
        # 判断缓存是否存在
        if context is None:
            # 缓存不存在,查询数据
            # 查询sku_id对应的商品SKU信息
            try:
                sku = GoodsSKU.objects.get(id=sku_id)
            except GoodsSKU.DoesNotExist:
                return redirect(reverse('goods:index'))

            # 查询所有商品分类信息
            categorys = GoodsCategory.objects.all()

            # 查询商品订单评论信息,
            # 将最新的显示在第一条,order_by('-create_time'),显示最新的30条
            # orders中有GoodsSKU外键
            good_orders = sku.ordergoods_set.all().order_by('-create_time')[:30]

            # 查询最新商品推荐,查询出sku对应的商品类别下的所有商品
            new_skus = GoodsSKU.objects.filter(category=sku.category).order_by('-create_time')[:2]

            # 查询其他规格商品(因为商品会有按克,盒,袋...分,或者有各种颜色)
            other_skus = GoodsSKU.objects.exclude(id=sku_id)  # 除当前id对应的sku外的其他sku

            context = {
                'sku':sku,
                'categorys':categorys,
                'good_orders':good_orders,
                'new_skus':new_skus,
                'other_skus':other_skus
            }

            # 加缓存,key,value,过期时间
            cache.set('detail_%s' % sku_id, context, 3600)


        # 购物车数据,初始化为0
        cart_num = 0
        # 如果已登录，查询购物车信息,记录用户的浏览记录
        if user.is_authenticated():
            # 创建redis链接
            redis_con = get_redis_connection('default')
            # 查询redis数据库中的数据,结果为字典,因为使用hash存的
            cart_dict = redis_con.hgetall('cart_%s' % user.id)
            # 遍历字典中的value,算出购物车的值
            for val in cart_dict.values():
                cart_num += val

            # 浏览记录的获取和保存
            # 存储在redis中，以列表形式存储，存储sku_id, "history_userid: [0,1,2,3,4,5]"
            # 移除已经存在在浏览列表中的商品浏览记录,去重复,0 的时候,去除重复只留一个
            redis_con.lrem('history_%s' % user.id, 0, sku_id)
            # 查询浏览记录的时候是取的左边5条,所以加浏览记录的时候,从左边lpush进去
            redis_con.lpush('history_%s' % user.id, sku_id)
            # 只保存五条,ltrim(key, start, end)修剪到指定范围内的元素,对已存在的list操作
            redis_con.ltrim('history_%s' % user.id, 0, 4)

        context.update(cart_num=cart_num)

        return render(request, 'detail.html')


# 首页
class IndexView(View):
    def get(self, request):
        '''主页查询数据'''

        # 先从缓存中读取数据
        context = cache.get('index_page_data')
        print(context)

        # 判断缓存中是否存在
        if context is None:
            print('没有缓存,开始缓存')

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

            # 上下文数据
            context = {
                'categorys': categorys,
                'banners': banners,
                'pbanners': pbanners
            }

            # 设置缓存数据,cache.set(缓存数据在数据库中的key, 缓存的数据, 缓存过期时间)
            cache.set('index_page_data', context, 3600)

        # 购物车数量,购物车数据不能缓存,因为是会实时变化的
        cart_num = 0
        user = request.user
        # 判断用户是否是登录用户
        if user.is_authenticated():
            # 获取购物车数据
            # 创建redis链接,在settings中有CACHES配置
            redis_con = get_redis_connection('default')
            # 查询redis数据库,获得购物车数据(字典类型)
            cart_dict = redis_con.hgetall('cart_%s' % user.id)
            # 遍历字典,取出所有value
            for val in cart_dict.values():
                cart_num += val



        # context中追加数据
        context.update(cart_num=cart_num)

        return render(request, 'index.html', context)
        # return render(request, 'index.html')

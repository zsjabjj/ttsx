import json

from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect

# Create your views here.
from django.views.generic import View

# def index(request):
#     return render(request, 'index.html')

from django_redis import get_redis_connection
# 商品类别
from goods.models import GoodsCategory
# 商品轮播
from goods.models import IndexGoodsBanner
# 主页商品分类
from goods.models import IndexCategoryGoodsBanner
# 商品促销活动
from goods.models import IndexPromotionBanner

# 详情页
from goods.models import GoodsSKU

# 购物车数据统计类
class BaseCartView(View):
    def get_cart_num(self, request):
        # 查询购物车数据
        cart_num = 0
        # 判断用户是否是登录用户
        if request.user.is_authenticated():
            user = request.user
            # 获取购物车数据
            # 创建redis链接,在settings中有CACHES配置
            redis_con = get_redis_connection('default')
            # 查询redis数据库,获得购物车数据(字典类型)
            cart_dict = redis_con.hgetall('cart_%s' % user.id)
            # 遍历字典,取出所有value
            for val in cart_dict.values():
                cart_num += int(val)
        else:
            # 未登录,购物车数据来自cookie
            cart_json = request.COOKIES.get('cart')  # --->json字符串'{'':'','':'',...}'

            print(cart_json)

            # 判断购物车cookie数据是否存在，有可能用户从来没有操作过购物车
            if cart_json:
                # cookie中已经有购物车数据,将json字符串转换为json字典类型
                cart_dict = json.loads(cart_json)
            else:
                cart_dict = dict()  # 设置空字典,备用

            print(cart_dict)

            for val in cart_dict.values():
                cart_num += int(val)

        return cart_num


# 商品列表页
class ListView(BaseCartView):
    def get(self, request, category_id, page_num):
        print(category_id, page_num)
        # category_id:表示从哪个分类里面进来的,page_num:用户选择的页码
        # 还有通过浏览器网址获得的sort排序方式,
        # localhost:8000/goods/list/category_id/page_num/?sort='默认，价格，人气'
        # 获取sort方式
        sort = request.GET.get('sort', 'default')  # 设置默认值,如果没有选择排序方式,就按默认排序

        # 校验参数
        # 校验是否有category_id对应的分类
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return redirect(reverse('goods:index'))

        cart_num = self.get_cart_num(request)

        # 查询所有商品分类
        categorys = GoodsCategory.objects.all()

        # 查询本类别中新品推荐,两条
        new_skus = GoodsSKU.objects.filter(category=category).order_by('-create_time')[:2]

        # 查询商品列表
        # 根据排序方式查询
        # 按价格排序查询,价格从低到高
        if sort == 'price':
            skus = GoodsSKU.objects.filter(category=category).order_by('price')
        # 按人气热度查询,从高到低排
        elif sort == 'hot':
            # print(sort)
            skus = GoodsSKU.objects.filter(category=category).order_by('-sales')
        else:  # 默认排序
            skus = GoodsSKU.objects.filter(category=category)
            sort = 'default'

        # 分页
        # 先要将page_num转成int类型,因为获取到的是字符串
        page_num = int(page_num)
        # 分页器对象,Paginator(分页的对象, 每页显示数量)
        paginator = Paginator(skus, 2)
        # 页对象
        # 方法page(m)：返回Page对象，表示第m页的数据，下标以1开始
        try:
            page_skus = paginator.page(page_num)
        except EmptyPage:  # 当向page()提供一个有效值，但是那个页面上没有任何对象时抛出
            page_skus = paginator.page(1)

        # 属性page_range：返回页码列表，从1开始，例如[1, 2, 3, 4]
        page_list = paginator.page_range

        # 构造上下文
        context = {
            'sort':sort,  # 排序
            'category':category,  # category_id对应的分类
            'cart_num':cart_num,  # 购物车
            'categorys':categorys,  # 所有商品分类
            'new_skus':new_skus,  # 新品推荐
            'skus':skus,  # 按排序后得到的sku
            'page_skus':page_skus,  # 第page_num页中的sku
            'page_list':page_list  # 页码的列表[1, 2, 3, 4...]
        }


        return render(request, 'list.html', context)


# 详情页
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
        print(sku_id)
        # 获取缓存
        context = cache.get('detail_%s' % sku_id)
        print(context)

        # 判断缓存是否存在
        if context is None:
            print('meiyou huancun')
            # 缓存不存在,查询数据
            # 查询sku_id对应的商品SKU信息
            try:
                sku = GoodsSKU.objects.get(id=sku_id)
                print(sku)
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
            # other_skus = GoodsSKU.objects.exclude(id=sku_id)  # 除当前id对应的sku外的其他sku
            other_skus = sku.goods.goodssku_set.exclude(id=sku_id)

            context = {
                'sku': sku,  # 商品SKU信息
                'categorys': categorys,  # 所有商品分类信息
                'good_orders': good_orders,  # 商品订单评论信息
                'new_skus': new_skus,  # 最新商品推荐
                'other_skus': other_skus  # 其他规格商品
            }

            # 加缓存,key,value,过期时间
            cache.set('detail_%s' % sku_id, context, 3600)

        # 购物车数据,初始化为0
        cart_num = 0
        # 如果已登录，查询购物车信息,记录用户的浏览记录
        if request.user.is_authenticated():
            user = request.user
            # 创建redis链接
            redis_con = get_redis_connection('default')
            # 查询redis数据库中的数据,结果为字典,因为使用hash存的
            cart_dict = redis_con.hgetall('cart_%s' % user.id)
            # 遍历字典中的value,算出购物车的值
            for val in cart_dict.values():
                cart_num += int(val)

            # 浏览记录的获取和保存
            # 存储在redis中，以列表形式存储，存储sku_id, "history_userid: [0,1,2,3,4,5]"
            # 移除已经存在在浏览列表中的商品浏览记录,去重复,0 的时候,去除重复只留一个
            redis_con.lrem('history_%s' % user.id, 0, sku_id)
            # 查询浏览记录的时候是取的左边5条,所以加浏览记录的时候,从左边lpush进去
            redis_con.lpush('history_%s' % user.id, sku_id)
            # 只保存五条,ltrim(key, start, end)修剪到指定范围内的元素,对已存在的list操作
            redis_con.ltrim('history_%s' % user.id, 0, 4)
        else:
            # 未登录,购物车数据来自cookie
            cart_json = request.COOKIES.get('cart')  # --->json字符串'{'':'','':'',...}'

            print(cart_json)

            # 判断购物车cookie数据是否存在，有可能用户从来没有操作过购物车
            if cart_json:
                # cookie中已经有购物车数据,将json字符串转换为json字典类型
                cart_dict = json.loads(cart_json)
            else:
                cart_dict = dict()  # 设置空字典,备用

            print(cart_dict)

            for val in cart_dict.values():
                cart_num += int(val)

        context.update({"cart_num": cart_num})
        print(context)

        return render(request, 'detail.html', context)


# 首页
class IndexView(BaseCartView):
    def get(self, request):
        '''主页查询数据'''
        print('shouye')
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
                'categorys': categorys,  # 商品类别信息
                'banners': banners,  # 商品轮播,幻灯片
                'pbanners': pbanners  # 促销活动
            }

            # 设置缓存数据,cache.set(缓存数据在数据库中的key, 缓存的数据, 缓存过期时间)
            cache.set('index_page_data', context, 3600)

        cart_num = self.get_cart_num(request)

        # context中追加数据
        context.update({"cart_num": cart_num})
        print(context)
        return render(request, 'index.html', context)
        # return render(request, 'index.html')

import json

from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views.generic import View
from django_redis import get_redis_connection

from goods.models import GoodsSKU


# 删除购物车数据
class DeleteCartView(View):
    def post(self, request):
        # 获取参数
        sku_id = request.POST.get('sku_id')
        # 校验参数
        if not sku_id:
            return JsonResponse({'code': 1, 'message': '参数错误'})
        # 判断是否登录
        if request.user.is_authenticated():
            # 登录就从redis中删除数据
            redis_con = get_redis_connection('default')
            # 删除sku_id对应的商品,如果存在就会删除,如果不存在,redis自动忽略
            redis_con.hdel('cart_%s' % request.user.id, sku_id)

            return JsonResponse({'code': 0, 'message': '删除成功'})
        else:
            # 未登录,就从cookie中删除
            cart_json = request.COOKIES.get('cart')
            # 判断是否有购物车cookie
            if cart_json:
                cart_dict = json.loads(cart_json)
                # 判断sku_id 对应的商品是否存在
                if sku_id in cart_dict:
                    del cart_dict[sku_id]

                    response = JsonResponse({'code': 0, 'message': '删除成功'})
                    response.set_cookie('cart', json.dumps(cart_dict))
                    return response
                return JsonResponse({'code': 6, 'message': '商品已删除'})


# 修改购物车信息
class UpdateCartView(View):
    def post(self, request):
        # 获取参数sku_id和count
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        print(sku_id, count)

        # 校验参数
        if not all([sku_id, count]):
            return JsonResponse({'code': 1, 'message': '参数不完整'})
        # 判断商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'code': 2, 'message': '商品不存在'})
        # count是否为整数
        try:
            count = int(count)
        except Exception:
            return JsonResponse({'code': 3, 'message': '商品数量有误'})
        # 判断库存
        if count > sku.stock:
            return JsonResponse({'code': 4, 'message': '库存不足'})
        # 判断用户是否登录
        if request.user.is_authenticated():
            # 登录状态,将数据存到redis中
            redis_con = get_redis_connection('default')
            redis_con.hset('cart_%s' % request.user.id, sku_id, count)
            return JsonResponse({'code': 0, 'message': '更新购物车成功'})
        else:  # 用户未登录
            # 存到cookie
            cart_json = request.COOKIES.get('cart')
            if cart_json:
                cart_dict = json.loads(cart_json)
            else:
                cart_dict = dict()
            cart_dict[sku_id] = count
            new_cart_json = json.dumps(cart_dict)
            response = JsonResponse({'code': 0, 'message': '更新购物车成功'})
            response.set_cookie('cart', new_cart_json)
            return response


# 显示购物车页面
class CartInfoView(View):
    def get(self, request):
        '''提供购物车页面'''
        # 判断用户是否登录,如果登录,数据来自redis
        # 如果未登录,数据来自cookie
        if request.user.is_authenticated():
            # 创建redis链接
            redis_con = get_redis_connection('default')
            # 获取redis中购物车数据
            cart_dict = redis_con.hgetall('cart_%s' % request.user.id)
        else:  # 用户未登录
            # cookie中查询购物车信息,结果为json字符串
            cart_json = request.COOKIES.get('cart')
            if cart_json:
                # 将json字符串转成json字典
                cart_dict = json.loads(cart_json)
            else:
                cart_dict = dict()

        # 需要商品sku和购物车商品数据
        # 先定义一个列表,存放sku
        skus = list()
        # 商品总价格
        total_amount = 0
        # 商品总数量
        total_count = 0
        # 获取sku_id和count
        for sku_id, count in cart_dict.items():
            try:
                sku = GoodsSKU.objects.get(id=sku_id)
            except GoodsSKU.DoesNotExist:
                # 商品不存在就继续遍历
                continue

            # count 装成数字类型
            count = int(count)
            # 一类商品的价格
            amount = sku.price * count
            # 将需要展示的数据保存到对象中,动态生成属性
            sku.amount = amount
            sku.count = count

            # 生成sku列表,此时的sku中有amount和count属性
            skus.append(sku)

            total_amount += amount
            total_count += count
            print(total_count, total_amount)

        # 构造上下文
        context = {
            'skus': skus,
            'total_amount': total_amount,
            'total_count': total_count
        }

        return render(request, 'cart.html', context)

        # def post(self, request):
        #     # 获取参数sku_id和count
        #     sku_id = request.POST.get('sku_id')
        #     count = request.POST.get('count')
        #     print(sku_id,count)
        #
        #     # 校验参数
        #     if not all([sku_id, count]):
        #         return JsonResponse({'code':1, 'message':'参数不完整'})
        #     # 判断商品是否存在
        #     try:
        #         sku = GoodsSKU.objects.get(id=sku_id)
        #     except GoodsSKU.DoesNotExist:
        #         return JsonResponse({'code':2, 'message':'商品不存在'})
        #     # count是否为整数
        #     try:
        #         count = int(count)
        #     except Exception:
        #         return JsonResponse({'code':3, 'message':'商品数量有误'})
        #     # 判断库存
        #     if count > sku.stock:
        #         return JsonResponse({'code':4, 'message':'库存不足'})
        #     # 判断用户是否登录
        #     if request.user.is_authenticated():
        #         # 登录状态,将数据存到redis中
        #         redis_con = get_redis_connection('default')
        #         redis_con.hset('cart_%s' % request.user.id, sku_id, count)
        #         return JsonResponse({'code':0, 'message':'更新购物车成功'})
        #     else:  # 用户未登录
        #         # 存到cookie
        #         cart_json = request.COOKIES.get('cart')
        #         if cart_json:
        #             cart_dict = json.loads(cart_json)
        #         else:
        #             cart_dict = dict()
        #         cart_dict[sku_id] = count
        #         new_cart_json = json.dumps(cart_dict)
        #         response = JsonResponse({'code':0, 'message':'更新购物车成功'})
        #         response.set_cookie('cart',new_cart_json)
        #         return response


# 添加商品进购物车
class AddCartView(View):
    """添加到购物车"""

    def post(self, request):

        # 接收数据：user_id，sku_id，count
        # 前端通过ajax发送post请求,并带有数据
        sku_id = request.POST.get('sku_id')
        print(sku_id)
        print(type(sku_id))
        count = request.POST.get('count')
        print(count)

        # 校验参数all()
        if not all([sku_id, count]):
            # code表示状态码,和前端商量决定
            return JsonResponse({'code': 1, 'message': '参数不完整'})

        # 判断商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)

        except GoodsSKU.DoesNotExist:
            return JsonResponse({'code': 2, 'message': '此商品不存在'})

        # 判断count是否是整数
        try:
            count = int(count)

        except Exception:
            return JsonResponse({'code': 3, 'message': '数量错误'})

        # 判断库存
        if count > sku.stock:
            return JsonResponse({'code': 4, 'message': '库存不足'})
        print('denglu')
        # 判断用户是否登陆
        if request.user.is_authenticated():
            # 只有在用户登录之后才有用户的id
            user_id = request.user.id

            # 操作redis数据库存储商品到购物车
            # 链接redis数据库
            redis_con = get_redis_connection('default')
            # 判断要添加进购物车的商品是否存在,如果不存在,返回None,存在返回sku_id对应的数量
            # hgetall(key)--->{field1:value1,field2:value2,...}
            # hget(key, field)--->field对应的value
            origin_count = redis_con.hget('cart_%s' % user_id, sku_id)

            print(origin_count)

            if origin_count:
                # 商品存在就将数量累加
                count += int(origin_count)  # origin_count为bytes类型
                print(count)
            # 购物车中此商品存在与否,最后都将数量保存
            # hash类型存储,key为cart_user_id, 属性为sku_id, 属性值为count
            redis_con.hset('cart_%s' % user_id, sku_id, count)

            # 为了配合前端展示商品在购物车的总数，后台需要查询购物车的所有的商品的数量求
            cart_num = 0
            # 获得user_id对应下的所有购物车中的商品
            cart_dict = redis_con.hgetall('cart_%s' % user_id)
            # cart_dict.values()--->获取字典中的value,返回列表
            for val in cart_dict.values():
                print(val)
                cart_num += int(val)
            print(cart_num)
            # json方式响应添加购物车结果
            return JsonResponse({'code': 0, 'message': '加入购物车成功', 'cart_num': cart_num})

        else:  # 用户未登录,将数据存在cookie中
            # return JsonResponse({'code': 5, 'message': '用户未登录'})
            # 如果用户未登录，就保存购物车数据到cookie中,cart:{sku_id1:10,sku_id2:20,...}
            # 先从cookie的购物车信息中，获取当前商品的购物车记录,即json字符串购物车数据
            # cart是在cookie中存数据的key
            cart_json = request.COOKIES.get('cart')  # --->json字符串'{'':'','':'',...}'

            print(cart_json)

            # 判断购物车cookie数据是否存在，有可能用户从来没有操作过购物车
            if cart_json:
                # cookie中已经有购物车数据,将json字符串转换为json字典类型
                cart_dict = json.loads(cart_json)
            else:
                cart_dict = dict()  # 设置空字典,备用

            print(cart_dict)

            # 判断要加入购物车的商品是否存在
            if sku_id in cart_dict:  # sku_id
                count += int(cart_dict[sku_id])
            # 将数据存入
            cart_dict[sku_id] = count
            # 将json字典装换成json字符串
            new_cart_json = json.dumps(cart_dict)
            # 计算购物车数据
            cart_num = 0
            for val in cart_dict.values():
                cart_num += int(val)

            response = JsonResponse({'code': 0, 'message': '加入购物车成功', 'cart_num': cart_num})

            # 将数据存入cookie中
            response.set_cookie('cart', new_cart_json)

            print(response, cart_num)

            return response

from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect

# Create your views here.
from django.views.generic import View
from django_redis import get_redis_connection

from goods.models import GoodsSKU

from users.models import Address
from utils.views import LoginRequiredMixin


# 订单页面必须要求用户是登录状态
# 所以继承自己做的一个类
# class PlaceOrderView(LoginRequiredMixin, View):
class PlaceOrderView(View):
    # 此时用户是登录状态
    # 获取参数,来自前端form表单,sku_ids,count
    # form表单提交时,会自动去收集name属性下的value值
    # 有两个地方可以进入用户提交订单页面
    # 1,来自购物车的去结算,sku_ids来自form表单,count来自redis
    # 2,来自详情页的立即购买,sku_ids和count都来自form表单
    def post(self, request):
        if request.user.is_authenticated():
            # 获取参数
            sku_ids = request.POST.get('sku_ids')
            # 如果来自购物车页面,count为None
            # 如果来自立即购买,count为带过来的数据
            count = request.POST.get('count')
            print(sku_ids, count)

            # 定义临时变量使用
            skus = list()
            # 总金额和总数量
            total_sku_amount = 0
            total_count = 0
            # 运费
            trans_cost = 10

            if not count:
                # 校验参数
                if not sku_ids:
                    return redirect(reverse('cart:info'))
                # 表示来自购物车
                for sku_id in sku_ids:
                    try:
                        sku = GoodsSKU.objects.get(id=sku_id)
                    except GoodsSKU.DoesNotExist:
                        return redirect(reverse('cart:info'))
                    # 以上通过,查询redis
                    redis_con = get_redis_connection('default')
                    cart_dict = redis_con.hgetall('cart_%s' % request.user.id)
                    # cart_dict中数据为bytes类型
                    sku_count = cart_dict.get(sku_id.encode())
                    sku_count = int(sku_count)

                    # 计算商品小计
                    amount = sku.price * sku_count

                    sku.count = sku_count
                    sku.amount = amount
                    skus.append(sku)

                    # 总金额和总数量
                    total_sku_amount += amount
                    total_count += sku_count



            else:  # 数据来自详情页的立即购买
                if not sku_ids:
                    # 反解析传参数args和kwargs
                    return redirect(reverse('goods:detail', args=sku_ids))
                for sku_id in sku_ids:
                    # 判断商品是否存在
                    try:
                        sku = GoodsSKU.objects.get(id=sku_id)
                    except GoodsSKU.DoesNotExist:
                        return redirect(reverse('goods:detail', args=sku_id))
                    # 判断商品数量是否为整数
                    try:
                        sku_count = int(count)
                    except Exception:
                        return redirect(reverse('goods:detail', args=sku_id))

                    # 计算商品小计
                    amount = sku.price * sku_count

                    sku.count = sku_count
                    sku.amount = amount
                    skus.append(sku)

                    # 总金额和总数量
                    total_sku_amount += amount
                    total_count += sku_count
            # 最终实际支付金额
            total_amount = total_sku_amount + trans_cost

            # 查询地址
            try:
                addr = Address.objects.filter(user=request.user).latest('create_time')
            except Address.DoesNotExist:
                return redirect(reverse('users:address'))

            # 构造上下文
            context = {
                'skus': skus,  # 用户列表
                'total_amount': total_amount,  # 实际总金额
                'address': addr,  # 用户收货地址
                'total_sku_amount': total_sku_amount,  # 小计总金额
                'total_count': total_count,  # 总数量
                'trans_cost': trans_cost,  # 运费
            }

            return render(request, 'place_order.html', context)
        else:

            return redirect(reverse('users:login'))

import json
import re
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse
from django_redis import get_redis_connection
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired
from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import render, redirect
from users.models import User
from django.views.generic import View
from Celery.tasks import send_active_email
from users.models import Address

from goods.models import GoodsSKU
from utils.views import LoginRequiredMixin


# Create your views here.
# 函数视图可以通过判断语句来区分http请求
# 类视图也可以,好处是类视图可以提高代码复用

# 显示注册页面和处理post请求
# def register(request):
#     # 从浏览器f12中可以看到,请求网页页面时,使用get请求
#     if request.method == 'GET':
#         return render(request,'register.html')
#
#     # 在提交用户注册信息时,需要用post来提交
#     if request.method == 'POST':
#         return HttpResponse('函数视图post')

# 展示个人信息
class UserInfoView(LoginRequiredMixin, View):
    # 查询用户信息并展示
    def get(self, request):
        # 获取当前登录的用户
        user = request.user

        # 获得当前用户的地址信息
        try:
            address = user.address_set.latest('create_time')
        except Address.DoesNotExist:
            address = None
        # 查询用户浏览记录信息：存储在redis中，以列表形式存储，存储sku_id, "history_userid: [0,1,2,3,4,5]"
        redis_conn = get_redis_connection('default')
        # 查询redis数据库中的浏览记录,查询最新的五条,将来保存记录时记得从左向右保存
        sku_ids = redis_conn.lrange('history_%s' % user.id, 0, 5)
        # 遍历sku_ids，分别取出每个sku_id,然后根据sku_id查询商品sku信息
        skuList = list()
        for sku_id in sku_ids:
            sku = GoodsSKU.objects.get(id=sku_id)
            skuList.append(sku)

        context = {'address': address, 'skuList': skuList}

        return render(request, 'user_center_info.html', context)


# 展示用户地址页面
class AddressView(LoginRequiredMixin, View):
    def get(self, request):
        # 到这里说明当前用户已登录
        # 获取当前登录的用户名
        user = request.user
        print(request.user)
        # 获取要显示的最新的收货信息
        # latest 按照时间排序，排序后获取最新的记录
        try:
            address = user.address_set.latest('create_time')
        except Address.DoesNotExist:
            address = None

        context = {'address': address}

        return render(request, 'user_center_site.html', context)

    def post(self, request):
        '''接收用户输入的收货信息'''
        # 获取用户输入的收货信息
        user = request.user
        recv_name = request.POST.get('recv_name')
        recv_addr = request.POST.get('recv_addr')
        zipcode = request.POST.get('zipcode')
        recv_tel = request.POST.get('recv_tel')

        # 校验信息是否为空
        if all([recv_name, recv_addr, zipcode, recv_tel]):
            # 保存信息到数据库 django 已经给了方法保存
            Address.objects.create(
                user=user,
                consignee=recv_name,
                consignee_add=recv_addr,
                consignee_tel=recv_tel,
                zip_code=zipcode
            )

        return redirect(reverse('users:address'))


# 退出登录
class LogoutView(View):
    # 退出登录本质：清除用户相关的session
    def get(self, request):
        logout(request)
        return redirect(reverse('goods:index'))
        # return HttpResponse('退出登录成功')


# 登录
class LoginView(View):
    def get(self, request):
        return render(request, 'login.html', {'succmsg': '注册成功'})

    def post(self, request):
        # 获取用户登录数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        remembered = request.POST.get('remembered')
        print(username, password, remembered)
        # 判断是否输入为空,all(iterable)
        if not all([username, password]):
            print('1')
            return redirect(reverse('users:login'))
        # 验证用户是否存在,django自带对象authenticate
        user = authenticate(username=username, password=password)
        if user is None:
            return render(request, 'login.html', {'errmsg': '用户名或密码不对'})
            # return HttpResponse('用户名或密码不对')
        # 判断是否为激活用户
        if user.is_active is False:
            return render(request, 'login.html', {'errmsg': '用户名未激活,请激活后登录'})
            # return HttpResponse('用户名未激活,请激活后登录')
        # 真正的登陆一个用户：就在在服务器和浏览器之间记录登陆状态，session和cookie
        # 提示 : django用户认证系统，提供的login方法，如果需要记录登陆状态，需要搭配django_redis一起使用
        login(request, user)
        # 判断用户是否勾选了记住用户
        # 不做判断处理,默认cookie中sessionid有效期为两周
        if remembered is None:
            # 参数为0,cookie中sessionid有效期在结束浏览会话后就会失效
            request.session.set_expiry(0)
        else:
            # 参数为3600*24*10,cookie中sessionid有效期为十天
            request.session.set_expiry(3600 * 24 * 10)

        # 合并登录和未登录状态下的购物车
        # 查询购物车数据
        # cookie
        cart_json = request.COOKIES.get('cart')
        if cart_json:
            cart_dict_cookie = json.loads(cart_json)
        else:
            cart_dict_cookie = dict()

        # redis
        redis_con = get_redis_connection('default')
        # cart_dict_redis中key和value为bytes类型
        cart_dict_redis = redis_con.hgetall('cart_%s' % user.id)

        # 将cookie中的数据合并到redis中,取cookie中的数据
        for sku_id, count in cart_dict_cookie.items():
            # 需要将cookie中的数据转换为bytes类型
            sku_id = sku_id.encode()
            # 判断cookie中的商品,是否在redis中存在
            if sku_id in cart_dict_redis:
                origin_count = cart_dict_redis[sku_id]
                count += int(origin_count)
            cart_dict_redis[sku_id] = count

        # 一次性向redis中添加多个key和value
        redis_con.hmset('cart_%s' % user.id, cart_dict_redis)

        # 登录后给的响应
        next = request.GET.get('next')
        if next:
            return redirect(next)
        print('2')
        return redirect(reverse('goods:index'))

        # return HttpResponse('登录成功')


# 发送邮件激活注册用户
class ActivateView(View):
    def get(self, request, token):
        print(request)
        # print(request.GET)
        print(User.objects.all())
        # 创建序列化器
        serializer = Serializer(settings.SECRET_KEY, 3600)
        # 将加密的解密,得到是一个字典{"confirm": self.id}
        # 捕获激活链接是否已过期
        try:
            ret = serializer.loads(token)
            # print(ret)
        except SignatureExpired:
            #
            return HttpResponse('激活链接已过期')
        # 获取id
        user_id = ret['confirm']
        print(user_id)
        # 获取user_id对应的用户
        # 捕获是否存在此用户
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return render(request, 'register.html', {'errmsg': '用户不存在,请注册'})
            # return HttpResponse('用户不存在')
        if user.is_active:
            return HttpResponse('已经激活')
        # 将对应的用户激活
        user.is_active = True
        # 保存激活后的状态
        user.save()
        return redirect(reverse('users:login'))
        # return HttpResponse('success active')


# 类视图需要继承基类View,比函数视图更具有复写性
class RegisterView(View):
    # 处理get请求,接收用户request
    def get(self, request):
        return render(request, 'register.html')

    # 处理post请求
    def post(self, request):
        # 获取用户输入的信息
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        print('%s---%s---%s---%s' % (username, password, email, allow))
        # 校验用户信息
        # 使用all(),当all括号中全有值,结果为真,有一为空,就为假
        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': '输入信息有误'})
            # return HttpResponse('用户信息输入有误')
        # 判断邮箱格式是否正确
        ret = re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email)
        if not ret:
            return render(request, 'register.html', {'errmsg': '输入邮箱地址格式不正确'})
            # return HttpResponse('输入的邮箱格式不正确')
        # 判断用户是否勾选了用户协议,如果没有勾选用户协议,allow获取到的值为None
        if allow == None:
            return render(request, 'register.html', {'errmsg': '请勾选用户协议'})
            # return HttpResponse('请勾选用户协议')

        # 保存数据
        # 使用系统自带的认证系统,使用create_user保存数据(username,email,password)
        try:
            user = User.objects.create_user(username, email, password)
        # 用以上方法保存数据,自动会将is_active设置为True
        # 将激活状态设置为False,只有在通过激活邮件激活后,才设置为True
        except IntegrityError:
            return render(request, 'register.html', {'errmsg': '用户名已存在'})
            # return HttpResponse('用户名已存在')
        user.is_active = False
        # 因为数据表中的属性进行了更改,所以需要再次保存数据
        user.save()
        # 生成激活口令token,用来给用户发激活邮件
        token = user.generate_active_token()
        # 给用户邮箱发送激活链接,使用celery模块处理
        send_active_email.delay(email, username, token)

        # 返回响应
        return redirect(reverse('users:login'))
        # return HttpResponse('用户已注册')

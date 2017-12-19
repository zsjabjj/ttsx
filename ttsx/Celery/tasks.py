import os
os.environ["DJANGO_SETTINGS_MODULE"] = "ttsx.settings"
# 放到Celery服务器上时添加的代码
# import django
# django.setup()

from django.template import loader
from goods.models import GoodsCategory, IndexGoodsBanner, IndexPromotionBanner, IndexCategoryGoodsBanner

from celery import Celery
# Celery()中需要两个参数,一个参数是异步任务执行的路径,另一个参数是存放任务的队列地址
# 使用一个叫broker(中间人)来协client(任务的发出者)和worker(任务的处理者)
# broker格式:broker = 'redis://密码@ip/数据库'(我们这里使用redis数据库来作为队列)
from django.conf import settings
from django.core.mail import send_mail

app = Celery('Celery.tasks', broker='redis://localhost/4')  # 此处因为没有对redis设置密码


@app.task
def send_active_email(to_email, user_name, token):
    '''发送激活邮件'''
    # subject = ''  # 标题
    subject = "天天生鲜用户激活1"  # 标题
    body = "test"  # 文本邮件体
    sender = settings.EMAIL_FROM  # 发件人
    receiver = [to_email]  # 接收人
    html_body = '<h1>尊敬的用户 %s, 感谢您注册天天生鲜！</h1>' \
                '<br/><p>请点击此链接激活您的帐号<a href="http://127.0.0.1:8000/users/active/%s">' \
                'http://127.0.0.1:8000/users/active/%s</a></p>' % (user_name, token, token)
    send_mail(subject, body, sender, receiver, html_message=html_body)


@app.task
def get_static_index():

    print('get_static_index_start')

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

    # 以上已经将需要的数据都查询出来了
    # 加载模板内容
    template = loader.get_template('static_index.html')

    # 在加载的模板中放入上下文数据,得到html数据
    html_data = template.render(context)

    # 决定存放静态文件的地址
    # settings中静态文件的头地址STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
    html_path = os.path.join(settings.STATICFILES_DIRS[0], 'index.html')

    # 将html数据写入静态文件中
    with open(html_path, 'w') as f:
        f.write(html_data)

    print('get_static_index_end')

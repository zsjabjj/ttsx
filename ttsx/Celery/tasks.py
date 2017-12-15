import os
os.environ["DJANGO_SETTINGS_MODULE"] = "ttsx.settings"
# 放到Celery服务器上时添加的代码
import django
django.setup()

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
    subject = "天天生鲜用户激活"  # 标题
    body = "test"  # 文本邮件体
    sender = settings.EMAIL_FROM  # 发件人
    receiver = [to_email]  # 接收人
    html_body = '<h1>尊敬的用户 %s, 感谢您注册天天生鲜！</h1>' \
                '<br/><p>请点击此链接激活您的帐号<a href="http://127.0.0.1:8000/users/active/%s">' \
                'http://127.0.0.1:8000/users/active/%s</a></p>' % (user_name, token, token)
    send_mail(subject, body, sender, receiver, html_message=html_body)

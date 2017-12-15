from django.conf.urls import url

from apps.users import views

urlpatterns = [
    # url(r'^register$', views.register),
    # url(r'^register$', views.RegisterView.as_view),
    # 因为Django 的URL 解析器将请求和关联的参数发送给一个可调用的函数而不是一个类
    # 所以基于类的视图有一个as_view() 类方法用来作为类的可调用入口。
    # 该as_view 入口点创建类的一个实例并调用dispatch() 方法。
    # dispatch 查看请求是GET 还是POST 等等，并将请求转发给相应的方法
    url(r'^register$', views.RegisterView.as_view(), name='register'),
    url(r'^login$', views.LoginView.as_view(), name='login'),
    url(r'^logout$', views.LogoutView.as_view(), name='logout'),
    url(r'^active/(.+)$', views.ActivateView.as_view(), name='active'),
    url(r'^address$', views.AddressView.as_view(), name='address'),
    url(r'^userinfo$', views.UserInfoView.as_view(), name='userinfo'),
]

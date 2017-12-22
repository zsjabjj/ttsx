from django.conf.urls import url

from apps.cart import views

urlpatterns = [
    url(r'^add$', views.AddCartView.as_view(), name='add'),
    url(r'^update$', views.UpdateCartView.as_view(), name='update'),
    url(r'^delete', views.DeleteCartView.as_view(), name='delete'),
    url(r'^$', views.CartInfoView.as_view(), name='info'),
]
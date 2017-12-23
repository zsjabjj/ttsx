from django.conf.urls import url

from apps.orders import views

urlpatterns = [
    url(r'^place$', views.PlaceOrderView.as_view(), name='place')
]
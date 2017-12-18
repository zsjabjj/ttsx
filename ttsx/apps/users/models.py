from django.conf import settings
from django.contrib.auth.models import AbstractUser
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.db import models


# Create your models here.
# 继承AbstractUser系统自带用户认证系统
# 需要在项目settings中进行配置
# 用户信息表,继承字段:用户名,密码,邮箱,权限,是否激活......
# 继承了一个父类后,不需要在添加models.Model,因为重复
from utils.models import BaseModel


class User(AbstractUser, BaseModel):
    class Meta:
        db_table = 'df_users'
        verbose_name = '用户信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username

    def generate_active_token(self):
        """生成激活令牌"""
        # 生成序列化器,传入混淆字符串和过期时间
        serializer = Serializer(settings.SECRET_KEY, 3600)
        # dumps()生成加密后的id,存入字典中
        token = serializer.dumps({"confirm": self.id})  # 返回bytes类型
        return token.decode()  # 解码


# 用户地址表,需要字段:收货人,收货人地址,收货人联系方式,用户id(外键)
class Address(BaseModel):
    consignee = models.CharField(max_length=20, verbose_name='收货人')
    consignee_add = models.CharField(max_length=256, verbose_name='收货人地址')
    consignee_tel = models.CharField(max_length=11, verbose_name='联系方式')
    zip_code = models.CharField(max_length=6, verbose_name='邮政编码')
    user = models.ForeignKey(User, verbose_name='所属用户')

    def __str__(self):
        return self.consignee

    class Meta:
        db_table = 'df_address'
        verbose_name = '收货地址'
        verbose_name_plural = verbose_name

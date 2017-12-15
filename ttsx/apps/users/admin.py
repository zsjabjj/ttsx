from django.contrib import admin

# Register your models here.

# from apps.users.models import User, Address
# 使用上面的导入方式,开启django会报错:RuntimeError: Conflicting 'user_groups' models in application 'users'
# 意思是模块冲突,因为在settings中已经将apps指定,虽然没有红色报错,但是开启django报错
#
from users.models import User, Address

admin.site.register(User)
admin.site.register(Address)
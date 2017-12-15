from django.contrib.auth.decorators import login_required


class LoginRequiredMixin(object):
    '''验证用户是否登录,使用login_required装饰器，装饰as_view()的结果'''
    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        return login_required(view)
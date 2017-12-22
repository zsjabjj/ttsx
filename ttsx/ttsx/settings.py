"""
Django settings for ttsx project.

Generated by 'django-admin startproject' using Django 1.8.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys
# 添加应用的头路径,可以在注册应用时直接使用应用名
sys.path.insert(1, os.path.join(BASE_DIR, 'apps'))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '$a=1vu(-f&!%q^+awq%t*oc@))*5=*p1=l6t%woq!30bd--^k4'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tinymce',  # 富文本编辑器
    'haystack',  # 全文检索框架
    # 加了apps路径,注册时直接写应用名称
    'users',
    'goods',
    'orders',
    'cart',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'ttsx.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ttsx.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'ttsx',
        'HOST':'localhost',
        'USER':'root',
        'PASSWORD':'mysql',
        'PORT':'3306',
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'zh-Hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# 讲认证引导到自己建立的模型类中
AUTH_USER_MODEL = 'users.User'

# 确定发邮件服务器,配置发送邮件服务器参数
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend' # 导入邮件模块
EMAIL_HOST = 'smtp.163.com' # 发邮件主机
EMAIL_PORT = 25 # 发邮件端口
EMAIL_HOST_USER = 'zsj888878@163.com' # 授权的邮箱
EMAIL_HOST_PASSWORD = 'zsj878888' # 邮箱授权时获得的密码，非注册登录密码
EMAIL_FROM = '天天生鲜<zsj888878@163.com>' # 发件人抬头

# 配置redis缓存
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://localhost:6379/5",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# Session
# http://django-redis-chs.readthedocs.io/zh_CN/latest/#session-backend

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# 用于指定装饰器@login_required验证失败后跳转到的路径
LOGIN_URL = '/users/login'

# 配置Django自定义的存储系统
DEFAULT_FILE_STORAGE = 'utils.fastdfs.storage.FastDFSStorage'
CLIENT_CONF = os.path.join(BASE_DIR, 'utils/fastdfs/client.conf')

SERVER_IP = 'http://0.0.0.0:8888/'

# 富文本编辑器的样式设置
TINYMCE_DEFAULT_CONFIG = {
  'theme': 'advanced', # 丰富样式
  'width': 600,
  'height': 400,
}

# 配置搜索引擎后端
HAYSTACK_CONNECTIONS = {
  'default': {
      # 使用whoosh引擎：提示，如果不需要使用jieba框架实现分词，就使用whoosh_backend
      'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
      # 'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
      # 索引文件路径
      'PATH': os.path.join(BASE_DIR, 'whoosh_index'),
  }
}
# 当添加、修改、删除数据时，自动生成索引
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'
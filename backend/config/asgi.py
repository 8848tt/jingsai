"""ASGI 入口：将 ``application`` 暴露为模块级可调用对象。"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()

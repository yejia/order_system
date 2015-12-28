# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
from celery import Celery

from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'order_system.settings')

celery = Celery('order_system')
celery.config_from_object('django.conf:settings')
celery.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


if __name__ == '__main__':
    celery.start()

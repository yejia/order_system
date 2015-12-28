# -*- coding: utf-8 -*-

## Broker settings.
BROKER_URL = "amqp://"

# List of modules to import when celery starts.
#CELERY_IMPORTS = ("scheduler.lib.trigger", )

#import os
#os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecomm.settings")

CELERY_IMPORTS = ("order.models", )

CELERY_TASK_SERIALIZER = 'json' #TODO:try pickle
CELERY_RESULT_SERIALIZER = 'json'

# CELERY_ANNOTATIONS = {
#     'trigger.no_payment': {'rate_limit': '5/s'}
# }



# from datetime import timedelta

# CELERYBEAT_SCHEDULE = {
#     'trigger.no_payment': {
#         'task': 'trigger.no_payment',
#         'schedule': timedelta(seconds=30),
#         'args': ()
#     },
# }

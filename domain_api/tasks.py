from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django_logging import log, ErrorLogObject


@shared_task
def add(x, y):
    log.debug({"request":{"x": x, "y": y}})
    return int(x) + int(y)

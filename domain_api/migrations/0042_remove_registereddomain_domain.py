# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-06-16 10:38
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('domain_api', '0041_auto_20170616_1037'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='registereddomain',
            name='domain',
        ),
    ]
# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-24 00:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domain_api', '0003_auto_20170223_0734'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='roid',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='registrant',
            name='roid',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]

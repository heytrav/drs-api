# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-29 03:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domain_api', '0005_nameserverhost_roid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ipaddress',
            name='ip',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name='ipaddress',
            unique_together=set([('ip', 'nameserver_host')]),
        ),
    ]

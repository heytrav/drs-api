# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-23 07:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domain_api', '0002_auto_20170222_1956'),
    ]

    operations = [
        migrations.AlterField(
            model_name='personaldetail',
            name='disclose_address',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='personaldetail',
            name='disclose_company',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='personaldetail',
            name='disclose_email',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='personaldetail',
            name='disclose_fax',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='personaldetail',
            name='disclose_name',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='personaldetail',
            name='disclose_telephone',
            field=models.BooleanField(default=False),
        ),
    ]
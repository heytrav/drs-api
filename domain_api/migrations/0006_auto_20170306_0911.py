# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-06 09:11
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('domain_api', '0005_auto_20170306_0841'),
    ]

    operations = [
        migrations.AddField(
            model_name='defaultaccounttemplate',
            name='provider',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='domain_api.DomainProvider'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='defaultaccounttemplate',
            unique_together=set([('project_id', 'provider', 'account_template')]),
        ),
    ]

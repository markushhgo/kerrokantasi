# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-05-15 11:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('democracy', '0045_add_subcomments_to_comments'),
    ]

    operations = [
        migrations.AlterField(
            model_name='section',
            name='n_comments',
            field=models.IntegerField(blank=True, db_index=True, default=0, editable=False, verbose_name='number of comments'),
        ),
        migrations.AlterField(
            model_name='sectioncomment',
            name='n_comments',
            field=models.IntegerField(blank=True, db_index=True, default=0, editable=False, verbose_name='number of comments'),
        ),
    ]

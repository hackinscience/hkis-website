# Generated by Django 2.1.3 on 2018-11-29 08:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0003_auto_20181128_2306'),
    ]

    operations = [
        migrations.AddField(
            model_name='exercise',
            name='initial_solution',
            field=models.TextField(default='#!/usr/bin/env python3\n\n'),
        ),
    ]
# Generated by Django 3.2.2 on 2021-11-27 15:31

import django.contrib.auth.models
from django.db import migrations
import hkis.models


class Migration(migrations.Migration):

    dependencies = [
        ('hkis', '0027_remove_user_public_profile'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='user',
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='userinfo',
            managers=[
                ('objects', hkis.models.UserManager()),
            ],
        ),
    ]

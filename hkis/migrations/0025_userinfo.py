# Generated by Django 3.2.2 on 2021-11-27 10:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hkis', '0024_auto_20211127_1123'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('points', models.FloatField(default=0)),
                ('rank', models.PositiveIntegerField(blank=True, null=True)),
                ('public_profile', models.BooleanField(default=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='hkis', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

# Generated by Django 3.2.2 on 2021-12-01 14:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hkis', '0006_auto_20211201_1431'),
    ]

    operations = [
        migrations.AddField(
            model_name='exercise',
            name='solved_by',
            field=models.IntegerField(default=0),
        ),
    ]

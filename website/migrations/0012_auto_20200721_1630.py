# Generated by Django 3.0.8 on 2020-07-21 14:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0011_auto_20200721_1628'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exercise',
            name='initial_solution',
            field=models.TextField(blank=True),
        ),
    ]
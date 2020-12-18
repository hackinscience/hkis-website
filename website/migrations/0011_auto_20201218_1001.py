# Generated by Django 3.1.2 on 2020-12-18 09:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0010_auto_20201214_1343'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='name',
            field=models.CharField(max_length=42),
        ),
        migrations.AlterUniqueTogether(
            name='membership',
            unique_together={('user', 'team')},
        ),
    ]

# Generated by Django 2.1 on 2019-01-18 21:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("website", "0006_exercise_slug")]

    operations = [
        migrations.AddField(
            model_name="exercise",
            name="is_published",
            field=models.BooleanField(default=False),
        )
    ]

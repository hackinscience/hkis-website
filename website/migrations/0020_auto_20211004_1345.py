# Generated by Django 3.2.2 on 2021-10-04 11:45

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0019_auto_20210507_1828'),
    ]

    operations = [
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.IntegerField()),
            ],
        ),
        migrations.AddField(
            model_name='answer',
            name='votes',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AddIndex(
            model_name='answer',
            index=models.Index(fields=['exercise', '-votes'], name='website_ans_exercis_d8ffb5_idx'),
        ),
        migrations.AddField(
            model_name='vote',
            name='answer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='website.answer'),
        ),
        migrations.AddField(
            model_name='vote',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]

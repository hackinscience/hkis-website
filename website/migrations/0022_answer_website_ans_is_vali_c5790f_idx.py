# Generated by Django 3.2.2 on 2021-11-02 14:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0021_answer_is_safe'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='answer',
            index=models.Index(fields=['is_valid', 'is_safe'], name='website_ans_is_vali_c5790f_idx'),
        ),
    ]

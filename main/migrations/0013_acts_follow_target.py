# Generated by Django 2.1.7 on 2019-02-27 16:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0012_acts_follow'),
    ]

    operations = [
        migrations.AddField(
            model_name='acts_follow',
            name='target',
            field=models.CharField(default='', max_length=10),
        ),
    ]

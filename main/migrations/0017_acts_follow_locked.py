# Generated by Django 2.1.7 on 2019-03-01 14:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0016_auto_20190228_1529'),
    ]

    operations = [
        migrations.AddField(
            model_name='acts_follow',
            name='locked',
            field=models.BooleanField(default=False),
        ),
    ]

# Generated by Django 2.1.7 on 2019-03-07 21:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0022_auto_20190305_1603'),
    ]

    operations = [
        migrations.AlterField(
            model_name='acts_follow',
            name='act',
            field=models.CharField(max_length=20),
        ),
    ]

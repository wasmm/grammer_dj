# Generated by Django 2.1.7 on 2019-02-24 19:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_auto_20190224_1934'),
    ]

    operations = [
        migrations.AddField(
            model_name='acts',
            name='status',
            field=models.CharField(default='added', max_length=10),
        ),
    ]

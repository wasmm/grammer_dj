# Generated by Django 2.1.7 on 2019-03-19 16:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0024_auto_20190310_2014'),
    ]

    operations = [
        migrations.AddField(
            model_name='stat',
            name='count_follow_geo',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='stat',
            name='count_follow_tag',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='acts_follow',
            name='act',
            field=models.CharField(choices=[('follow_acc_acc', 'Целевой аккаунт'), ('follow_acc_geo', 'Целевой город'), ('follow_acc_tag', 'Целевой тег')], max_length=20),
        ),
    ]

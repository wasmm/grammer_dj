# Generated by Django 2.1.7 on 2019-02-27 09:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0009_stat_date_stat'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notices',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(default='', max_length=10)),
                ('message', models.CharField(default='', max_length=512)),
                ('dt_motice', models.DateTimeField(blank=True, null=True)),
                ('id_conn', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.Conn_inst_acc')),
            ],
        ),
    ]
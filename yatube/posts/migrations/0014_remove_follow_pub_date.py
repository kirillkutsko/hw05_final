# Generated by Django 2.2.16 on 2022-05-18 22:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0013_auto_20220519_0010'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='follow',
            name='pub_date',
        ),
    ]
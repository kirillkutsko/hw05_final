# Generated by Django 2.2.16 on 2022-05-18 21:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0012_auto_20220518_2337'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='follow',
            options={'verbose_name': 'Администрирование подписки', 'verbose_name_plural': 'Администрирование подписок'},
        ),
        migrations.AlterUniqueTogether(
            name='follow',
            unique_together=set(),
        ),
    ]

# Generated by Django 4.2.2 on 2024-05-07 14:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0025_alter_linksqueue_owner_id_alter_linksqueue_post_id'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='linksqueue',
            options={'verbose_name': 'Ссылка', 'verbose_name_plural': 'Ссылки'},
        ),
        migrations.AlterModelOptions(
            name='taskstorage',
            options={'verbose_name': 'Задание', 'verbose_name_plural': 'Задания'},
        ),
    ]

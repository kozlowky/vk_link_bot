# Generated by Django 4.2.2 on 2024-02-08 01:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0008_taskstorage_task_completed'),
    ]

    operations = [
        migrations.AddField(
            model_name='linkstorage',
            name='code',
            field=models.CharField(default=' ', max_length=10, unique=True, verbose_name='Код ссылки'),
            preserve_default=False,
        ),
    ]

# Generated by Django 4.2.2 on 2024-03-05 01:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0019_linkstorage_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='linksqueue',
            name='chat_type',
            field=models.CharField(default='', max_length=10, verbose_name='Тип чата'),
            preserve_default=False,
        ),
    ]

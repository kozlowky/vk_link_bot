# Generated by Django 4.2.2 on 2024-06-19 01:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0044_alter_taskstorage_link'),
    ]

    operations = [
        migrations.CreateModel(
            name='MessageLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chat_id', models.BigIntegerField()),
                ('message_data', models.JSONField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]

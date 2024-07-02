# Generated by Django 4.2.2 on 2024-06-25 06:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0051_remove_messagelog_chat_id_messagelog_chat'),
    ]

    operations = [
        migrations.AlterField(
            model_name='linksqueue',
            name='bot_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='links_queues', to='bot.botuser', verbose_name='Пользователь'),
        ),
        migrations.AlterField(
            model_name='taskstorage',
            name='bot_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='task_storage', to='bot.botuser', verbose_name='Пользователь'),
        ),
    ]
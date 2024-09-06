# Generated by Django 4.2.2 on 2024-09-06 07:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0053_add_messages_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='botuser',
            name='state_menu',
            field=models.IntegerField(choices=[(0, 'DEFAULT'), (1, 'VK_LINK'), (2, 'VIP_CODE'), (3, 'STATUS'), (4, 'RESET_LINK'), (5, 'ACCEPT_TASK_MANUALLY'), (6, 'GET_TASK_LINKS')], default=0, verbose_name='Состояние'),
        ),
    ]
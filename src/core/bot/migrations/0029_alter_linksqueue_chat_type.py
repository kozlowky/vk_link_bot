# Generated by Django 4.2.2 on 2024-05-08 02:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0028_alter_botuser_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='linksqueue',
            name='chat_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='chat_type', to='bot.chat', verbose_name='Тип чата'),
        ),
    ]

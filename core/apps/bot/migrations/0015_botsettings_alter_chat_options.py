# Generated by Django 4.2.2 on 2024-03-04 09:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0014_rename_botsettings_chat'),
    ]

    operations = [
        migrations.CreateModel(
            name='BotSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.AlterModelOptions(
            name='chat',
            options={'verbose_name': 'Чат', 'verbose_name_plural': 'Чаты'},
        ),
    ]

# Generated by Django 4.2.2 on 2024-06-19 01:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0046_alter_messagelog_options'),
    ]

    operations = [
        migrations.DeleteModel(
            name='MessageLog',
        ),
    ]

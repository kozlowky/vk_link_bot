# Generated by Django 4.2.2 on 2024-02-05 01:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0004_linksqueue_link_priority_linksqueue_queue_number_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='botuser',
            name='vip_end_date',
            field=models.DateField(blank=True, null=True, verbose_name='Дата окончания VIP кода'),
        ),
    ]

# Generated by Django 5.1.6 on 2025-03-14 14:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0011_alter_order_options_remove_order_order_status_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('conformed', 'Confirmed'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled')], default='pending', max_length=20),
        ),
    ]

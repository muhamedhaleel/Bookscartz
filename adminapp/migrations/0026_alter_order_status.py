# Generated by Django 5.1.6 on 2025-03-22 06:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0025_remove_order_return_action_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('returned', 'Returned'), ('cancelled', 'Cancelled')], default='pending', max_length=20),
        ),
    ]

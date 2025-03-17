# Generated by Django 5.1.6 on 2025-03-15 12:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0024_alter_returnrequest_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled'), ('returned', 'Returned')], default='pending', max_length=20),
        ),
    ]

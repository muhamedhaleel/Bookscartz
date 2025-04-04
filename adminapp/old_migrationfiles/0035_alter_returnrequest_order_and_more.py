# Generated by Django 5.1.6 on 2025-03-29 11:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0034_alter_returnrequest_order_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='returnrequest',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='return_request', to='adminapp.order'),
        ),
        migrations.AlterField(
            model_name='returnrequest',
            name='order_item',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='return_request', to='adminapp.orderitem'),
        ),
    ]

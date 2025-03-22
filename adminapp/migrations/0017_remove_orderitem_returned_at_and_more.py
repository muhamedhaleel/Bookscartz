# Generated by Django 5.1.6 on 2025-03-21 06:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0016_returnrequest_refund_amount_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderitem',
            name='returned_at',
        ),
        migrations.RemoveField(
            model_name='returnrequest',
            name='refund_amount',
        ),
        migrations.RemoveField(
            model_name='returnrequest',
            name='refunded_at',
        ),
        migrations.AddField(
            model_name='returnrequest',
            name='admin_notes',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='returnrequest',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='return_request', to='adminapp.order'),
        ),
    ]

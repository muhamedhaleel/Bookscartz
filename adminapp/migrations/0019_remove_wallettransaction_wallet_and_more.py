# Generated by Django 5.1.6 on 2025-03-21 13:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0018_returnrequest_refund_amount_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='wallettransaction',
            name='wallet',
        ),
        migrations.RemoveField(
            model_name='wallettransaction',
            name='order',
        ),
        migrations.RemoveField(
            model_name='returnrequest',
            name='refund_amount',
        ),
        migrations.RemoveField(
            model_name='returnrequest',
            name='refunded_at',
        ),
        migrations.DeleteModel(
            name='Wallet',
        ),
        migrations.DeleteModel(
            name='WalletTransaction',
        ),
    ]

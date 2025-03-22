# Generated by Django 5.1.6 on 2025-03-22 06:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0021_order_return_action_orderitem_return_action_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='return_action',
            field=models.CharField(choices=[('none', 'None'), ('Return', 'Return'), ('Return Rejected', 'Return Rejected')], default='none', max_length=20),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='return_action',
            field=models.CharField(choices=[('none', 'None'), ('Return', 'Return'), ('Return Rejected', 'Return Rejected')], default='none', max_length=20),
        ),
    ]

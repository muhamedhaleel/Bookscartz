# Generated by Django 5.1.6 on 2025-03-14 18:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0015_alter_order_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='return_requested',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='return_status',
            field=models.CharField(choices=[('none', 'No Return'), ('requested', 'Return Requested'), ('approved', 'Return Approved'), ('rejected', 'Return Rejected')], default='none', max_length=20),
        ),
        migrations.AlterModelTable(
            name='orderitem',
            table=None,
        ),
    ]

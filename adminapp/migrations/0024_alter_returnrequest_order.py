# Generated by Django 5.1.6 on 2025-03-15 09:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0023_alter_returnrequest_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='returnrequest',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='return_request', to='adminapp.order'),
        ),
    ]

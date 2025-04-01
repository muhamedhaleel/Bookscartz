# Generated by Django 5.1.6 on 2025-03-30 09:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0045_remove_product_secondary_language'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='primary_language',
            field=models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='primary_products', to='adminapp.language'),
        ),
        migrations.AddField(
            model_name='product',
            name='secondary_language',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='secondary_products', to='adminapp.language'),
        ),
    ]

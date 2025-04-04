# Generated by Django 5.1.6 on 2025-04-01 04:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0054_language_added_on_alter_language_name_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='language',
            name='added_on',
        ),
        migrations.AlterField(
            model_name='language',
            name='name',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='product',
            name='name',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='product',
            name='primary_language',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='primary_products', to='adminapp.language'),
        ),
        migrations.AlterField(
            model_name='product',
            name='secondary_language',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='secondary_products', to='adminapp.language'),
        ),
        migrations.AlterField(
            model_name='product',
            name='tertiary_language',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tertiary_products', to='adminapp.language'),
        ),
    ]

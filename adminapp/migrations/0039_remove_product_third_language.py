# Generated by Django 5.1.6 on 2025-03-29 19:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0038_remove_product_additional_languages_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='third_language',
        ),
    ]

# Generated by Django 5.1.6 on 2025-03-21 05:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0013_wallet_wallettransaction'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='returnrequest',
            name='admin_notes',
        ),
        migrations.AddField(
            model_name='orderitem',
            name='returned_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='returnrequest',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='returnrequest',
            name='comments',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='returnrequest',
            name='reason',
            field=models.TextField(),
        ),
    ]

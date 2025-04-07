from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0002_alter_cartitem_unique_together'),
    ]

    operations = [
        migrations.AlterField(
            model_name='returnrequest',
            name='order_item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='return_request', to='adminapp.orderitem'),
        ),
    ] 
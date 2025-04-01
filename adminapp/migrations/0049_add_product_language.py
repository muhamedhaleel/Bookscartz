from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0048_product_secondary_language'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='language',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='adminapp.language'
            ),
        ),
    ]
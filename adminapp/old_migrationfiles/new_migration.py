from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0048_product_secondary_language'),
    ]

    operations = [
        migrations.RunSQL(
            """
            -- Drop foreign key constraint if exists
            SET @constraint_name = (
                SELECT CONSTRAINT_NAME
                FROM information_schema.KEY_COLUMN_USAGE
                WHERE TABLE_NAME = 'adminapp_product'
                AND COLUMN_NAME = 'language_id'
                AND CONSTRAINT_NAME != 'PRIMARY'
                AND TABLE_SCHEMA = DATABASE()
                LIMIT 1
            );
            SET @drop_fk = IF(@constraint_name IS NOT NULL,
                CONCAT('ALTER TABLE adminapp_product DROP FOREIGN KEY ', @constraint_name),
                'SELECT 1');
            PREPARE stmt FROM @drop_fk;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;

            -- Drop the column if exists
            SET @column_exists = (SELECT COUNT(*)
                FROM information_schema.COLUMNS
                WHERE TABLE_NAME = 'adminapp_product'
                AND COLUMN_NAME = 'language_id'
                AND TABLE_SCHEMA = DATABASE());
            SET @drop_column = IF(@column_exists > 0,
                'ALTER TABLE adminapp_product DROP COLUMN language_id',
                'SELECT 1');
            PREPARE stmt FROM @drop_column;
            EXECUTE stmt;
            DEALLOCATE PREPARE stmt;
            """
        )
    ]

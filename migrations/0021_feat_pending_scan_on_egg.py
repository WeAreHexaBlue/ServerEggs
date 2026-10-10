from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('eggs', '0020_battle_set_null_on_delete')]

    initial = False

    operations = [
        ops.AddField(
            model_name='Egg',
            name='pending_scan',
            field=fields.BooleanField(default=False, null=True),
        ),
        ops.RunSQL(sql="""
            UPDATE egg
            SET pending_scan = false
            WHERE pending_scan IS NULL
        """),
        ops.AlterField(
            model_name='Egg',
            name='pending_scan',
            field=fields.BooleanField(default=False, null=False)
        ),
    ]

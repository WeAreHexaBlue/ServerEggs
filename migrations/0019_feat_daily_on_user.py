from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise import fields
from tortoise.indexes import Index

class Migration(migrations.Migration):
    dependencies = [('eggs', '0018_change_allow_user_lang_allow_ext_lang')]

    initial = False

    operations = [
        ops.AddField(
            model_name='User',
            name='allow_explicit_dms',
            field=fields.BooleanField(default=False, null=True),
        ),
        ops.RunSQL(sql="""
            UPDATE "user"
            SET allow_explicit_dms = false
            WHERE allow_explicit_dms IS NULL;
        """),
        ops.AlterField(
            model_name='User',
            name='allow_explicit_dms',
            field=fields.BooleanField(default=False, null=False)
        ),
        ops.AddField(
            model_name='User',
            name='last_daily_at',
            field=fields.DatetimeField(null=True, db_index=True),
        ),
        ops.AddIndex(
            model_name='User',
            index=Index(fields=['last_daily_at']),
        ),
    ]

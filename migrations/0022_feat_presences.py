from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('eggs', '0021_feat_pending_scan_on_egg')]

    initial = False

    operations = [
        ops.CreateModel(
            name='Presence',
            fields=[
                ('id', fields.BigIntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('text', fields.TextField(unique=False)),
                ('info', fields.TextField(null=True, unique=False)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
            ],
            options={'table': 'presence', 'app': 'eggs', 'pk_attr': 'id'},
            bases=['Model'],
        )
    ]

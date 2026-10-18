from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('eggs', '0023_feat_code_on_presence')]

    initial = False

    operations = [
        ops.CreateModel(
            name='EmbedHost',
            fields=[
                ('id', fields.BigIntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('host', fields.CharField(unique=True, max_length=253)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
            ],
            options={'table': 'embedhost', 'app': 'eggs', 'pk_attr': 'id'},
            bases=['Model'],
        )
    ]

from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('eggs', '0022_feat_presences')]

    initial = False

    operations = [
        ops.AddField(
            model_name='Presence',
            name='code',
            field=fields.TextField(null=True, unique=False),
        ),
    ]

from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise import fields
from tortoise.indexes import Index

class Migration(migrations.Migration):
    dependencies = [('eggs', '0017_feat_lang_on_egg')]

    initial = False

    operations = [
        ops.RenameField(
            model_name='Guild',
            old_name='allow_user_lang',
            new_name='allow_ext_lang',
        )
    ]

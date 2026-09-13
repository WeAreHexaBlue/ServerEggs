from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise import fields
from tortoise.indexes import Index

class Migration(migrations.Migration):
    dependencies = [('eggs', '0016_feat_channel_ratings_on_guild')]

    initial = False

    operations = [
        ops.AddField(
            model_name='Egg',
            name='lang',
            field=fields.CharField(default='en', max_length=5, null=True),
        ),
        ops.RunSQL(sql="""
            UPDATE egg
            SET lang = 'en'
            WHERE lang IS NULL
        """),
        ops.AlterField(
            model_name="Egg",
            name="lang",
            field=fields.CharField(default="en", max_length=5, null=False)
        )
    ]

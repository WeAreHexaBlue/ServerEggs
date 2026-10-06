from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise.fields.base import OnDelete
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('eggs', '0019_feat_daily_on_user')]

    initial = False

    operations = [
        ops.AlterField(
            model_name='Battle',
            name='egg_a',
            field=fields.ForeignKeyField('eggs.Egg', source_field='egg_a_id', null=True, db_constraint=True, to_field='id', related_name='battles_as_a', on_delete=OnDelete.SET_NULL),
        ),
        ops.AlterField(
            model_name='Battle',
            name='egg_b',
            field=fields.ForeignKeyField('eggs.Egg', source_field='egg_b_id', null=True, db_constraint=True, to_field='id', related_name='battles_as_b', on_delete=OnDelete.SET_NULL),
        ),
        ops.AlterField(
            model_name='Battle',
            name='user_a',
            field=fields.ForeignKeyField('eggs.User', source_field='user_a_id', null=True, db_constraint=True, to_field='id', related_name='challenges_sent', on_delete=OnDelete.SET_NULL),
        ),
        ops.AlterField(
            model_name='Battle',
            name='user_b',
            field=fields.ForeignKeyField('eggs.User', source_field='user_b_id', null=True, db_constraint=True, to_field='id', related_name='challenges_received', on_delete=OnDelete.SET_NULL),
        ),
        ops.AlterField(
            model_name='Battle',
            name='winner',
            field=fields.ForeignKeyField('eggs.Egg', source_field='winner_id', null=True, db_constraint=True, to_field='id', related_name='battle_wins', on_delete=OnDelete.SET_NULL),
        ),
        ops.AlterField(
            model_name='Battle',
            name='winner_user',
            field=fields.ForeignKeyField('eggs.User', source_field='winner_user_id', null=True, db_constraint=True, to_field='id', related_name='user_battle_wins', on_delete=OnDelete.SET_NULL),
        ),
        ops.RunSQL(
            sql="""
                DO $$
                DECLARE r RECORD;
                BEGIN
                    FOR r IN
                        SELECT c.conname AS conname
                        FROM pg_constraint c
                        JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = c.conkey[1]
                        WHERE c.conrelid = 'battle'::regclass AND c.contype = 'f'
                            AND a.attname IN ('egg_a_id', 'egg_b_id', 'user_a_id', 'user_b_id', 'winner_id', 'winner_user_id')
                    LOOP
                        EXECUTE format('ALTER TABLE "battle" DROP CONSTRAINT %I', r.conname);
                    END LOOP;
                END $$;
                ALTER TABLE "battle" ADD CONSTRAINT "fk_battle_egg_a" FOREIGN KEY ("egg_a_id") REFERENCES "egg" ("id") ON DELETE SET NULL;
                ALTER TABLE "battle" ADD CONSTRAINT "fk_battle_egg_b" FOREIGN KEY ("egg_b_id") REFERENCES "egg" ("id") ON DELETE SET NULL;
                ALTER TABLE "battle" ADD CONSTRAINT "fk_battle_user_a" FOREIGN KEY ("user_a_id") REFERENCES "user" ("id") ON DELETE SET NULL;
                ALTER TABLE "battle" ADD CONSTRAINT "fk_battle_user_b" FOREIGN KEY ("user_b_id") REFERENCES "user" ("id") ON DELETE SET NULL;
                ALTER TABLE "battle" ADD CONSTRAINT "fk_battle_winner" FOREIGN KEY ("winner_id") REFERENCES "egg" ("id") ON DELETE SET NULL;
                ALTER TABLE "battle" ADD CONSTRAINT "fk_battle_winner_user" FOREIGN KEY ("winner_user_id") REFERENCES "user" ("id") ON DELETE SET NULL;
            """,
            reverse_sql="""
                ALTER TABLE "battle" DROP CONSTRAINT "fk_battle_egg_a";
                ALTER TABLE "battle" DROP CONSTRAINT "fk_battle_egg_b";
                ALTER TABLE "battle" DROP CONSTRAINT "fk_battle_user_a";
                ALTER TABLE "battle" DROP CONSTRAINT "fk_battle_user_b";
                ALTER TABLE "battle" DROP CONSTRAINT "fk_battle_winner";
                ALTER TABLE "battle" DROP CONSTRAINT "fk_battle_winner_user";
                ALTER TABLE "battle" ADD FOREIGN KEY ("egg_a_id") REFERENCES "egg" ("id") ON DELETE CASCADE;
                ALTER TABLE "battle" ADD FOREIGN KEY ("egg_b_id") REFERENCES "egg" ("id") ON DELETE CASCADE;
                ALTER TABLE "battle" ADD FOREIGN KEY ("user_a_id") REFERENCES "user" ("id") ON DELETE CASCADE;
                ALTER TABLE "battle" ADD FOREIGN KEY ("user_b_id") REFERENCES "user" ("id") ON DELETE CASCADE;
                ALTER TABLE "battle" ADD FOREIGN KEY ("winner_id") REFERENCES "egg" ("id") ON DELETE CASCADE;
                ALTER TABLE "battle" ADD FOREIGN KEY ("winner_user_id") REFERENCES "user" ("id") ON DELETE CASCADE;
            """,
        ),
    ]

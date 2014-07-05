"""Add promotion tables.

Revision ID: 15ac6dc43be
Revises: b2d9902312
Create Date: 2014-06-27 13:56:35.834588

"""

# revision identifiers, used by Alembic.
revision = '15ac6dc43be'
down_revision = 'b2d9902312'

from alembic import op
import sqlalchemy as sa

promotions = sa.sql.table('promotions',
    sa.Column('id', sa.Integer()),
    sa.Column('identifier', sa.Unicode()),
    sa.Column('name', sa.Unicode(length=30)),
    sa.Column('is_public', sa.Boolean()),
    sa.Column('price', sa.Integer()),
    sa.Column('hidden_ability', sa.Integer()),
    sa.Column('start_date', sa.Date()),
    sa.Column('end_date', sa.Date()),
)

promotion_recipients = sa.sql.table('promotion_recipients',
    sa.Column('promotion_id', sa.Integer()),
    sa.Column('trainer_id', sa.Integer()),
    sa.Column('received', sa.Boolean()),
)

promotion_pokemon_species = sa.sql.table('promotion_pokemon_species',
    sa.Column('promotion_id', sa.Integer()),
    sa.Column('pokemon_species_id', sa.Integer()),
)

trainers = sa.sql.table('trainers',
    sa.Column('id', sa.Integer()),
    sa.Column('is_newbie', sa.Boolean())
)

pokemon_species = sa.sql.table('pokemon_species',
    sa.Column('id', sa.Integer()),
    sa.Column('is_starter', sa.Boolean())
)

def upgrade():
    promotions_id_seq = sa.Sequence('promotions_id_seq')
    op.execute(sa.schema.CreateSequence(promotions_id_seq))

    op.create_table('promotions',
        sa.Column('id', sa.Integer(), promotions_id_seq, nullable=False),
        sa.Column('identifier', sa.Unicode(), nullable=False),
        sa.Column('name', sa.Unicode(length=30), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('price', sa.Integer(), nullable=False),
        sa.Column('hidden_ability', sa.Boolean(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('identifier'),
        sa.UniqueConstraint('identifier'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('name')
    )

    op.create_table('promotion_recipients',
        sa.Column('promotion_id', sa.Integer(), nullable=False),
        sa.Column('trainer_id', sa.Integer(), nullable=False),
        sa.Column('received', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['promotion_id'], ['promotions.id']),
        sa.ForeignKeyConstraint(['trainer_id'], ['trainers.id']),
        sa.PrimaryKeyConstraint('promotion_id', 'trainer_id')
    )

    op.create_table('promotion_pokemon_species',
        sa.Column('promotion_id', sa.Integer(), nullable=False),
        sa.Column('pokemon_species_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['pokemon_species_id'], ['pokemon_species.id']),
        sa.ForeignKeyConstraint(['promotion_id'], ['promotions.id']),
        sa.PrimaryKeyConstraint('promotion_id', 'pokemon_species_id')
    )

    op.create_table('promotion_items',
        sa.Column('promotion_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], ),
        sa.ForeignKeyConstraint(['promotion_id'], ['promotions.id'], ),
        sa.PrimaryKeyConstraint('promotion_id', 'item_id')
    )

    # Add the newbie promotion
    op.bulk_insert(promotions, [{
        'id': 1,
        'identifier': 'newbie-deal',
        'name': 'Newbie deal',
        'is_public': True,
        'price': 15,
        'hidden_ability': False,
        'start_date': None,
        'end_date': None
    }])

    op.execute(
        promotion_pokemon_species.insert().from_select(
            ['promotion_id', 'pokemon_species_id'],

            sa.sql.select([1, pokemon_species.c.id])
                .where(pokemon_species.c.is_starter == True)
        )
    )
        
    op.execute(
        promotion_recipients.insert().from_select(
            ['promotion_id', 'trainer_id', 'received'],

            sa.sql.select([1, trainers.c.id, True])
                .where(trainers.c.is_newbie == False)
        )
    )

    op.drop_column('pokemon_species', 'is_starter')
    op.drop_column('trainers', 'is_newbie')


def downgrade():
    op.add_column('trainers', sa.Column('is_newbie', sa.Boolean))
    op.add_column('pokemon_species', sa.Column('is_starter', sa.Boolean))

    non_newbies = (
        sa.sql.select([promotion_recipients.c.trainer_id])
        .where(promotion_recipients.c.promotion_id == 1)
    )

    op.execute(
        trainers.update()
        .values({'is_newbie': ~trainers.c.id.in_(non_newbies)})
    )

    starters = (
        sa.sql.select([promotion_pokemon_species.c.pokemon_species_id])
        .where(promotion_pokemon_species.c.promotion_id == 1)
    )

    op.execute(
        pokemon_species.update()
        .values({'is_starter': pokemon_species.c.id.in_(starters)})
    )

    op.drop_table('promotion_items')
    op.drop_table('promotion_pokemon_species')
    op.drop_table('promotion_recipients')
    op.drop_table('promotions')
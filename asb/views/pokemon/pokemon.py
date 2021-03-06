from pyramid.view import view_config
import sqlalchemy as sqla

from . import can_evolve
from asb import db
from asb.resources import PokemonIndex


@view_config(context=PokemonIndex, renderer='/indices/pokemon.mako')
def pokemon_index(context, request):
    """The index page for everyone's Pokémon."""

    pokemon = (
        db.DBSession.query(db.Pokemon)
        .join(db.Pokemon.trainer)
        .filter(db.Trainer.is_validated, ~db.Trainer.ban.has())
        .join(db.PokemonForm)
        .join(db.PokemonSpecies)
        .order_by(db.PokemonSpecies.order, db.Pokemon.name)
        .options(
            sqla.orm.joinedload('gender'),
            sqla.orm.joinedload('trainer'),
            sqla.orm.joinedload('form'),
            sqla.orm.joinedload('form.species'),
            sqla.orm.joinedload('ability'),
            sqla.orm.joinedload('item')
        )
        .all()
    )

    return {'pokemon': pokemon}

@view_config(context=db.Pokemon, renderer='/pokemon.mako')
def pokemon(pokemon, request):
    """An individual Pokémon's info page."""

    evo_info = {}

    for evo in pokemon.species.evolutions:
        if evo.evolution_method is None:
            continue

        if evo.evolution_method.happiness:
            evo_info['happiness'] = evo.evolution_method.happiness

        if evo.evolution_method.experience:
            evo_info['experience'] = evo.evolution_method.experience

    return {'pokemon': pokemon, 'can_evolve': can_evolve(pokemon),
        'evo_info': evo_info}

@view_config(name='sigstuff', context=db.Pokemon, renderer='/sig_stuff.mako')
def sig_stuff(pokemon, request):
    """A page for viewing a Pokémon's body modification and move modification,
    if any.
    """

    return {'pokemon': pokemon, 'movemod': pokemon.move_modification,
        'bodmod': pokemon.body_modification}

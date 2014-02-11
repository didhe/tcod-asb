<%inherit file='/base.mako'/>\
<%namespace name="helpers" file="/helpers.mako"/>\
<%block name='title'>${ability.name} - Abilities - The Cave of Dragonflies ASB</%block>\

<h1>${ability.name}</h1>
<p>${ability.description}</p>

<h1>Pokémon</h1>
${helpers.pokemon_form_table(normal_pokemon, hidden_pokemon,
    subheaders=('Regular ability', 'Hidden ability'), squashed_forms=True)}
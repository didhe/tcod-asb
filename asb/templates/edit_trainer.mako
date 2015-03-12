<%inherit file='/base.mako'/>\
<%namespace name="h" file="/helpers/helpers.mako"/>\
<%block name='title'>Edit ${trainer.name} - Trainers - The Cave of Dragonflies ASB</%block>\

<h1>Edit ${trainer.name}</h1>

<form action="${request.path}" method="POST">
${form.csrf_token()}
${h.form_error_list(*form.errors.values())}

<dl>
    <dt>${form.roles.label}</dt>
    <dd>${form.roles(class_='option-list')}</dd>
</dl>

${form.save()}
</form>


<h2>Money</h2>
<form action="${request.path}" method="POST">
${money_form.csrf_token()}
${h.form_error_list(*money_form.errors.values())}
<dl>
    <dt>Current balance</dt>
    <dd>$${trainer.money}</dd>

    <dt>Add/subtract</dt>
    <dd>
        +$${money_form.add(size=2, maxlength=3)} or
        −$${money_form.subtract(size=2, maxlength=3)}
    </dd>

    <dt>${money_form.note.label}</dt>
    <dd>${money_form.note(size=60)}</dd>
</dl>

${money_form.submit}
</form>

import random

import pyramid.httpexceptions as httpexc
from pyramid.view import view_config
import sqlalchemy as sqla
import sqlalchemy.orm
import wtforms

from asb import db
import asb.forms
import asb.tcodf
from asb.resources import TrainerIndex

class TrainerEditForm(asb.forms.CSRFTokenForm):
    """A form for editing a trainer.

    To be expanded as need arises.
    """

    roles = asb.forms.MultiCheckboxField('Roles')

    trainer_item = None
    item = wtforms.StringField(validators=[wtforms.validators.Optional()])
    item_recipient = asb.forms.TrainerField()

    save = wtforms.SubmitField('Save')

    def set_roles(self, trainer):
        """Set the choices for the roles field."""

        self.roles.choices = (
            db.DBSession.query(db.Role.identifier, db.Role.name)
            .order_by(db.Role.id)
            .all()
        )

        if self.roles.data is None:
            self.roles.data = [role.identifier for role in trainer.roles]

    def get_item(self, trainer):
        """Fetch the named item from the trainer's bag, if possible."""

        if self.item.data:
            self.trainer_item = (
                db.DBSession.query(db.TrainerItem)
                .filter_by(trainer_id=trainer.id, pokemon_id=None)
                .join(db.Item)
                .filter(sqla.func.lower(db.Item.name) ==
                        self.item.data.lower())
                .first()
            )

    def validate_item(form, field):
        """Make sure an item was found.

        n.b. the Optional validator will go first.
        """

        if form.trainer_item is None:
            raise wtforms.validators.ValidationError('Item not found in bag')

    def validate_item_recipient(form, field):
        """Make sure the intended recipient actually exists, if an item is
        being moved.
        """

        if form.trainer_item is not None and field.trainer is None:
            raise wtforms.validators.ValidationError('Unknown username')

class TrainerMoneyForm(asb.forms.CSRFTokenForm):
    """A form for manually giving a trainer money."""

    add = wtforms.IntegerField(validators=[
        wtforms.validators.Optional(),
        wtforms.validators.NumberRange(min=1, message='$1 minimum')
    ])

    subtract = wtforms.IntegerField(validators=[
        wtforms.validators.Optional(),
        wtforms.validators.NumberRange(min=1, message='$1 minimum')
    ])

    note = wtforms.StringField(
        'Note (required)',
        [wtforms.validators.Required()],
        filters=[lambda note: note if note is None else note.strip()]
    )

    submit = wtforms.SubmitField('Cha-ching')

    def validate_subtract(form, field):
        """Complain if a number has been entered in both money_add and
        money_subtract.
        """

        if form.add.data:
            raise wtforms.validators.ValidationError(
                "You can't add and subtract money in one transaction."
            )

class TrainerPasswordResetForm(asb.forms.CSRFTokenForm):
    """A form for resetting a trainer's password."""

    confirm = wtforms.BooleanField("Yes, I want to reset this user's password",
                                   [wtforms.validators.Required()])
    reset = wtforms.SubmitField('Reset')

class TrainerBanForm(asb.forms.CSRFTokenForm):
    """A form for banning a trainer.

    TODO: Implement *un*-banning, if we ever need it.
    """

    confirm = wtforms.BooleanField(validators=[wtforms.validators.Required()])
    reason = wtforms.StringField('Reason', [wtforms.validators.Required()])
    ban = wtforms.SubmitField('Ban')

def random_password():
    """Return a random sixteen-character alphanumeric password."""

    return ''.join(
        random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                      'abcdefghijklmnopqrstuvwxyz'
                      '0123456789')
        for n in range(16)
    )

@view_config(context=TrainerIndex, renderer='/indices/trainers.mako')
def trainer_index(context, request):
    """The index of all the trainers in the league."""

    pokemon_count = (
        db.DBSession.query(db.Pokemon.trainer_id, sqla.func.count('*')
            .label('count'))
        .select_from(db.Pokemon)
        .group_by(db.Pokemon.trainer_id)
        .subquery()
    )

    trainers = (
        db.DBSession.query(db.Trainer, pokemon_count.c.count)
        .select_from(db.Trainer)
        .join(pokemon_count, pokemon_count.c.trainer_id == db.Trainer.id)
        .options(sqla.orm.subqueryload('squad'))
        .filter(db.Trainer.is_validated, ~db.Trainer.ban.has())
        .order_by(db.Trainer.name)
        .all()
    )

    return {'trainers': trainers}

@view_config(context=db.Trainer, renderer='/trainer.mako')
def trainer(trainer, request):
    """A trainer's info page."""

    profile_link = asb.tcodf.user_forum_link(trainer.tcodf_user_id)
    return {'trainer': trainer, 'profile_link': profile_link}

@view_config(name='edit', context=db.Trainer, renderer='/edit_trainer.mako',
  request_method='GET', permission='trainer.edit')
def edit(trainer, request):
    """A page for editing a trainer."""

    # XXX This is getting to be a lot of forms; it might actually be easier at
    # this point to just make them all one form and complicate validation a bit
    stuff = {
        'trainer': trainer,
        'form': TrainerEditForm(prefix='edit', csrf_context=request.session),
        'money_form': TrainerMoneyForm(
            prefix='money', csrf_context=request.session
        ),
        'password_form': TrainerPasswordResetForm(
            prefix='password', csrf_context=request.session
        ),
        'ban_form': TrainerBanForm(prefix='ban', csrf_context=request.session)
    }

    stuff['form'].set_roles(trainer)
    return stuff

@view_config(name='edit', context=db.Trainer, renderer='/edit_trainer.mako',
  request_method='POST', permission='trainer.edit')
def edit_commit(trainer, request):
    """Process a request to edit a trainer."""

    # Get ye forms
    form = TrainerEditForm(request.POST, prefix='edit',
                           csrf_context=request.session)
    form.set_roles(trainer)
    form.get_item(trainer)
    money_form = TrainerMoneyForm(request.POST, prefix='money',
                                  csrf_context=request.session)
    password_form = TrainerPasswordResetForm(request.POST, prefix='password',
                                             csrf_context=request.session)
    ban_form = TrainerBanForm(request.POST, prefix='ban',
                              csrf_context=request.session)

    return_dict = {'trainer': trainer, 'form': form, 'money_form': money_form,
                   'password_form': password_form, 'ban_form': ban_form}

    if form.save.data:
        # Handle the main edit form
        if not form.validate():
            return return_dict

        # Update roles
        if form.roles.data is not None:
            trainer.roles = (
                db.DBSession.query(db.Role)
                .filter(db.Role.identifier.in_(form.roles.data))
                .all()
            )

        # Move item
        if form.trainer_item is not None:
            form.trainer_item.trainer_id = form.item_recipient.trainer.id
    elif money_form.submit.data:
        # Handle the money form
        if not money_form.validate():
            return return_dict

        amount = money_form.add.data or -money_form.subtract.data

        transaction = db.BankTransaction(
            trainer_id=trainer.id,
            amount=amount,
            state='from-mod',
            approver_id=request.user.id
        )
        db.DBSession.add(transaction)
        db.DBSession.flush()

        note = db.BankTransactionNote(
            bank_transaction_id=transaction.id,
            trainer_id=request.user.id,
            note=money_form.note.data
        )
        db.DBSession.add(note)

        trainer.money += amount
    elif password_form.reset.data:
        # Handle the password reset form
        if not password_form.validate():
            return return_dict

        password = random_password()
        trainer.set_password(password)
        request.session.flash("{0}'s temporary password is: {1}"
                              .format(trainer.name, password))
    elif ban_form.ban.data:
        # Handle the ban form
        if not ban_form.validate():
            return return_dict

        db.DBSession.add(db.BannedTrainer(
            trainer_id=trainer.id,
            banned_by_trainer_id=request.user.id,
            reason = ban_form.reason.data
        ))

    # Calling it like this avoids the trailing slash and thus a second redirect
    return httpexc.HTTPSeeOther(
        request.resource_path(trainer.__parent__, trainer.__name__)
    )

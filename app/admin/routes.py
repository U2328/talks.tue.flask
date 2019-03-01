from flask import render_template, request, redirect,\
                  url_for, abort
from flask_login import current_user

from . import bp
from .forms import TalkForm, SpeakerForm, TagForm
from app import db
from app.utils import is_safe_url, copy_row
from app.api.routes import TalkTable, SpeakerTable, TagTable
from app.auth.utils import has_perms
from app.auth.models import Permission
from app.core.models import Talk, Speaker, Tag, HistoryItem
from app.core.utils import add_historyitem


__all__ = (
    'index',
    'tag',
    'talk',
    'speaker'
)


@bp.route('/', methods=['GET'])
@has_perms(Permission.ADMIN)
def index():
    return render_template(
        'admin/index.html',
        title="Admin",
        talk_table=TalkTable,
        speaker_table=SpeakerTable,
        tag_table=TagTable,
        tag_form=TagForm(),
        history_items=HistoryItem.query.order_by(HistoryItem.timestamp.desc())[:10]
    )


@bp.route('/tag', methods=['POST'])
@has_perms(Permission.ADMIN)
def tag():
    form = TagForm(request.form)
    if form.validate_on_submit():
        tag = Tag()
        form.populate_obj(tag)
        db.session.add(tag)
        db.session.commit()
        next = request.args.get('next')
        if not is_safe_url(next):
            return abort(400)
        return redirect(next or url_for('admin.index'))
    return redirect(url_for('admin.index'))


@bp.route('/talk', methods=['GET', 'POST'])
@bp.route('/talk/<int:id>', methods=['GET', 'POST'])
@has_perms(Permission.ADMIN)
def talk(id=None):
    talk = Talk() if id is None else Talk.query.get(id)
    if talk is None and id is not None:
        return abort(404)
    if request.args.get('copy', False):
        talk = copy_row(talk, ['id'])

    is_new = talk.id is None
    form = TalkForm(obj=talk)

    if form.validate_on_submit():
        old = hash(talk)
        form.populate_obj(talk)
        if form.password.data:
            talk.set_password(form.password.data)
        talk.viewable = True
        changed = old != hash(talk)

        if changed or is_new:
            add_historyitem(
                talk, "",
                HistoryItem.Types.CREATE
                if is_new else
                HistoryItem.Types.EDIT
            )

        if is_new:
            db.session.add(talk)
        db.session.commit()

        next = request.args.get('next')
        if not is_safe_url(next):
            return abort(400)
        return redirect(next or url_for('admin.index'))

    return render_template('admin/talk.html', title="Talk - Admin", form=form, new=is_new)


@bp.route('/speaker', methods=['GET', 'POST'])
@bp.route('/speaker/<int:id>', methods=['GET', 'POST'])
@has_perms(Permission.ADMIN)
def speaker(id=None):
    speaker = Speaker() if id is None else Speaker.query.get(id)
    if speaker is None and id is not None:
        return abort(404)
    if request.args.get('copy', False):
        speaker = copy_row(speaker, ['id'])

    is_new = speaker.id is None
    form = SpeakerForm(obj=speaker)

    if form.validate_on_submit():
        old = hash(speaker)
        form.populate_obj(speaker)
        if form.password.data:
            speaker.set_password(form.password.data)
        speaker.viewable = True
        changed = old != hash(speaker)

        if changed or is_new:
            add_historyitem(
                speaker, "",
                HistoryItem.Types.CREATE
                if is_new else
                HistoryItem.Types.EDIT
            )

        if is_new:
            db.session.add(speaker)
        db.session.commit()

        next = request.args.get('next')
        if not is_safe_url(next):
            return abort(400)
        return redirect(next or url_for('admin.index'))

    return render_template('admin/speaker.html', title="Speaker - Admin", form=form, new=is_new)

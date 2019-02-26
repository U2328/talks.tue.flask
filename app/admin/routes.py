from flask import render_template, request, redirect, url_for, abort,current_app

from . import bp
from .forms import TalkForm, SpeakerForm, TagForm
from app import db
from app.utils import is_safe_url, copy_row
from app.api.routes import TalkTable, SpeakerTable, TagTable
from app.auth.utils import has_perms
from app.core.models import Talk, Speaker, Tag


@bp.route('/', methods=['GET'])
@has_perms('admin')
def index():
    return render_template(
        'admin/index.html',
        title="Admin",
        talk_table=TalkTable,
        speaker_table=SpeakerTable,
        tag_table=TagTable,
        tag_form=TagForm()
    )


@bp.route('/tag', methods=['POST'])
@has_perms('admin')
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
@has_perms('admin')
def talk(id=None):
    if request.method == 'GET':
        talk = Talk() if id is None else Talk.query.get(id)
        if talk is None:
            return abort(404)
        if request.args.get('copy', False):
            talk = copy_row(Talk, talk, ['id'])
            db.session.add(talk)
            db.session.commit()
            current_app.logger.info(talk)
            return redirect(url_for('admin.talk', id=talk.id))
        if id is None:
            db.session.add(talk)
            db.session.commit()
        form = TalkForm(obj=talk)
        is_new = id is None
    elif request.method == 'POST':
        form = TalkForm(request.form)
        if form.validate():
            talk = Talk.query.get(form.id.data)
            if talk is None:
                return abort(400) if id is None else abort(404)
            form.populate_obj(talk)
            if form.password.data:
                talk.set_password(form.password.data)
            db.session.commit()
            next = request.args.get('next')
            if not is_safe_url(next):
                return abort(400)
            return redirect(next or url_for('admin.index'))
        is_new = False
    return render_template('admin/talk.html', title="Talk - Admin", form=form, new=is_new)


@bp.route('/speaker', methods=['GET', 'POST'])
@bp.route('/speaker/<int:id>', methods=['GET', 'POST'])
@has_perms('admin')
def speaker(id=None):
    if request.method == 'GET':
        speaker = Speaker() if id is None else Speaker.query.get(id)
        if speaker is None:
            return abort(404)
        if request.args.get('copy', False):
            speaker = copy_row(Speaker, speaker, ['id'])
            db.session.add(speaker)
            db.session.commit()
            current_app.logger.info(speaker)
            return redirect(url_for('admin.speaker', id=speaker.id))
        if id is None:
            db.session.add(speaker)
            db.session.commit()
        form = SpeakerForm(obj=speaker)
        is_new = id is None
    elif request.method == 'POST':
        form = SpeakerForm(request.form)
        if form.validate():
            speaker = Speaker.query.get(form.id.data)
            if speaker is None:
                return abort(400) if id is None else abort(404)
            form.populate_obj(speaker)
            if form.password.data:
                speaker.set_password(form.password.data)
            db.session.commit()
            next = request.args.get('next')
            if not is_safe_url(next):
                return abort(400)
            return redirect(next or url_for('admin.index'))
        is_new = False
    return render_template('admin/speaker.html', title="Speaker - Admin", form=form, new=is_new)

from flask import render_template, request, redirect, url_for, abort,current_app

from . import bp
from .forms import TalkForm, SpeakerForm
from app import db
from app.utils import is_safe_url
from app.api.routes import TalkTable, SpeakerTable
from app.auth.utils import has_perms
from app.core.models import Talk, Speaker


@bp.route('/', methods=['GET'])
@has_perms('admin')
def index():
    return render_template('admin/index.html', title="Admin", talk_table=TalkTable, speaker_table=SpeakerTable)


@bp.route('/talk', methods=['GET', 'POST'])
@bp.route('/talk/<int:id>', methods=['GET', 'POST'])
@has_perms('admin')
def talk(id=None):
    talk = None if id is None else Talk.query.filter_by(id=id).first()
    form = TalkForm(request.form, obj=talk)
    if form.validate_on_submit():
        if talk is None:
            talk = Talk(
                name=form.name.data,
                timestamp=form.timestamp.data,
                description=form.description.data,
                _tags=form.tags.data,
                speaker=form.speaker.data
            )
            talk.set_password(form.password.data)
            db.session.add(talk)
        else:
            form.populate_obj(talk)
            talk.set_password(form.password.data)
        db.session.commit()
        next = request.args.get('next')
        if not is_safe_url(next):
            return abort(400)
        return redirect(next or url_for('admin.index'))
    return render_template('admin/talk.html', title="Talk - Admin", form=form, new=talk is None)


@bp.route('/speaker', methods=['GET', 'POST'])
@bp.route('/speaker/<int:id>', methods=['GET', 'POST'])
@has_perms('admin')
def speaker(id=None):
    speaker = None if id is None else speaker.query.filter_by(id=id).first()
    form = SpeakerForm(request.form, obj=speaker)
    if form.validate_on_submit():
        if speaker is None:
            speaker = Speaker(
                name=form.name.data,
                familiy_name=form.familiy_name.data,
                about_me=form.about_me.data,
            )
            speaker.set_password(form.password.data)
            db.session.add(speaker)
        else:
            form.populate_obj(speaker)
            speaker.set_password(form.password.data)
        db.session.commit()
        next = request.args.get('next')
        if not is_safe_url(next):
            return abort(400)
        return redirect(next or url_for('admin.index'))
    return render_template('admin/speaker.html', title="speaker - Admin", form=form, new=speaker is None)

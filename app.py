import db as models
import hmac
import logging
import os
import re
from datetime import datetime
from db import db
from dropbox import Dropbox
from dropbox.files import Metadata
from dropbox.exceptions import ApiError
from flask import abort, Flask, redirect, render_template, request, url_for
from hashlib import sha256
from logging.handlers import RotatingFileHandler
from pushbullet import Pushbullet
from reverse_proxy import ReverseProxied
from typing import List
from waitress import serve


app = Flask(__name__)
app.wsgi_app = ReverseProxied(app.wsgi_app)
app.config.update(
    DEBUG=os.getenv('DEBUGGING', 'N') == 'Y',
    SECRET_KEY=os.getenv('SECRET_KEY', 'fZ9Wk3ha#Ose%4H&!tPtBE&5FBuKHd'),
    SQLALCHEMY_DATABASE_URI='sqlite:///{0}'.format(
        os.path.join(os.path.dirname(os.path.realpath(__file__)),  'app.db')
    ),
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)
with app.app_context():
    db.init_app(app)
    db.create_all()

file_handler = RotatingFileHandler(os.path.join(os.path.dirname(
    os.path.realpath(__file__)), 'todo-remind.log'), maxBytes=50000, backupCount=2)
formatter = logging.Formatter(
    '[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
app.logger.addHandler(file_handler)
app.logger.setLevel('DEBUG')
app.logger.info('Starting ToDo Remind...')


@app.route('/')
def main():
    """Show main page"""
    return render_template('main.html')


@app.route('/config')
def config():
    """Show application configuration"""
    dropbox = db.session.query(models.Dropbox).first()  # type: models.Dropbox
    pushbullet = db.session.query(models.Pushbullet).first()  # type: models.Pushbullet
    return render_template('config.html', dropbox=dropbox, pushbullet=pushbullet)


@app.route('/config/update', methods=['POST'])
def config_update():
    """Update application configuration"""
    to_save = request.form.to_dict()

    dropbox = db.session.query(models.Dropbox).first()  # type: models.Dropbox
    is_new = dropbox is None
    if is_new:
        dropbox = models.Dropbox()
    dropbox.key = to_save['dropbox[key]']
    dropbox.secret = to_save['dropbox[secret]']
    dropbox.access_token = to_save['dropbox[access_token]']
    dropbox.file_location = to_save['dropbox[file_location]']
    if is_new:
        db.session.add(dropbox)
    else:
        db.session.merge(dropbox)

    pushbullet = db.session.query(models.Pushbullet).first()  # type: models.Pushbullet
    is_new = pushbullet is None
    if is_new:
        pushbullet = models.Pushbullet()
    pushbullet.access_token = to_save['pushbullet[access_token]']
    if is_new:
        db.session.add(pushbullet)
    else:
        db.session.merge(pushbullet)
    db.session.commit()

    return redirect(url_for('config'))


@app.route('/todos')
def todos():
    todos = db.session.query(models.ToDo)  # type: List[models.ToDo]
    return render_template('todos.html', todos=todos)


def get_datetime(value):
    """Convert string to datetime, defaulting to 8:00am if no time is specified"""
    try:
        return datetime.strptime(value, '%Y-%m-%d-%H%M')
    except ValueError:
        pass
    return datetime.strptime(value+'-0800', '%Y-%m-%d-%H%M')


def update_todos(content):
    """Update todos from content"""
    now = datetime.now()
    search = re.compile('^(?!x )(.+) notify:(\S+)', re.IGNORECASE)
    lines = [s.strip() for s in content.splitlines()]
    todos = []
    for line in lines:
        match = search.match(line.decode('utf-8'))
        if match is None:
            continue
        try:
            todo = models.ToDo()
            todo.text = match.group(1)
            todo.date_time = get_datetime(match.group(2))
            if todo.date_time < now:
                continue
            todos.append(todo)
            found_todo = db.session.query(models.ToDo).filter(
                models.ToDo.text == todo.text
            ).first()  # type: models.ToDo
            if found_todo is None or found_todo.date_time != todo.date_time:
                send_notification('Todo Reminder Added', body=todo.text)
        except ValueError:
            pass

    models.ToDo.query.delete()  # Clear out current todos
    for todo in todos:
        db.session.add(todo)
    db.session.commit()


@app.route('/sync', methods=['GET', 'POST'])
def sync():
    challenge = request.args.get('challenge')
    if challenge is not None:
        return challenge

    """Synchronize database with todo.txt"""
    dropbox = db.session.query(models.Dropbox).first()  # type: models.Dropbox

    # Make sure this is a valid request from Dropbox
    signature = request.headers.get('X-Dropbox-Signature')
    if not hmac.compare_digest(signature, hmac.new(dropbox.secret.encode(), request.data, sha256).hexdigest()):
        app.logger.warn('Invalid sync request attempted')
        abort(403)

    dbx = Dropbox(dropbox.access_token)
    if dropbox.cursor is None:
        result = dbx.files_list_folder(path=os.path.dirname(dropbox.file_location))
    else:
        result = dbx.files_list_folder_continue(cursor=dropbox.cursor)

    # Check if todo.txt was changed
    found = False
    for metadata in result.entries:  # type: Metadata
        if metadata.path_lower == dropbox.file_location.lower():
            found = True
            break
    if not found:
        dropbox.cursor = result.cursor
        db.session.merge(dropbox)
        db.session.commit()
        return ''

    app.logger.info('Sync request made')

    try:
        md, res = dbx.files_download(path=dropbox.file_location)
    except ApiError as err:
        if err.error.is_path() and err.error.get_path().is_not_found():
            return 'File not found: ' + dropbox.file_location
        return 'Other error occurred'
    update_todos(content=res.content)

    dropbox.cursor = result.cursor
    db.session.merge(dropbox)
    db.session.commit()
    return ''


@app.route('/debug')
def debug():
    """Debug todo synchronization code"""
    dropbox = db.session.query(models.Dropbox).first()  # type: models.Dropbox
    try:
        dbx = Dropbox(dropbox.access_token)
        md, res = dbx.files_download(path=dropbox.file_location)
    except ApiError as err:
        if err.error.is_path() and err.error.get_path().is_not_found():
            return 'File not found: ' + dropbox.file_location
        return 'Other error occurred'
    update_todos(content=res.content)
    return redirect(url_for('todos'))


def send_notification(title, body, pb=None):
    """Send notification via Pushbullet"""
    if pb is None:
        pushbullet = db.session.query(models.Pushbullet).first()  # type: models.Pushbullet
        pb = Pushbullet(pushbullet.access_token)
    return pb.push_note(title=title, body=body)


@app.cli.command()
def notify():
    """Find and send notifications"""
    now = datetime.now().replace(second=0, microsecond=0)
    notifications = db.session.query(models.ToDo).filter(
        models.ToDo.date_time == now
    )  # type: List[models.ToDo]
    if notifications is None:
        return
    pushbullet = db.session.query(models.Pushbullet).first()  # type: models.Pushbullet
    pb = Pushbullet(pushbullet.access_token)
    for notification in notifications:
        send_notification(title='Todo Reminder', body=notification.text, pb=pb)
        db.session.delete(notification)
    db.session.commit()


if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000)

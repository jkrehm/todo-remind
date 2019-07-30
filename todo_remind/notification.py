from pushbullet import Pushbullet
from todo_remind import db as models
from todo_remind.db import db


def send_notification(title, body):
    # TODO cache `pb` when application starts, and bust if access token changes
    pushbullet = db.session.query(models.Pushbullet).first()  # type: models.Pushbullet
    pb = Pushbullet(pushbullet.access_token)
    return pb.push_note(title=title, body=body)

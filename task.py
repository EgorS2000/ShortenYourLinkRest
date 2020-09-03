from ShortenYourLink import db
from ShortenYourLink.models import Link

from celery import Celery
from celery.schedules import crontab
from datetime import datetime


CELERY_BROKER_URL = 'amqp://rabbitmq:rabbitmq@rabbit:5672/'
CELERY_RESULT_BACKEND = 'rpc://'

app = Celery(
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Minsk',
    enable_utc=True,
)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):

    sender.add_periodic_task(
        crontab(hour=19, minute=36, day_of_week='*/1'),
        test.s(),
    )


@app.task
def test():
    dead_links = []
    for link in Link.query.all():
        if link.life_time_end > datetime.utcnow():
            dead_links.append(link)
    try:
        for link in dead_links:
            db.session.delete(link)

        db.session.commit()
    except:
        return "Can not delete links"

    return "Links deleted successful"


#celery -A task beat --loglevel=info
#celery -A task worker --loglevel=info
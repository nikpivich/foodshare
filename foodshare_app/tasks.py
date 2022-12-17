from foodshare.celery import app
from faker import Faker
from django.contrib.auth import get_user_model
from .models import Post
from django.contrib.auth.hashers import make_password

User = get_user_model()


@app.task(ignore_result=True)
def fake_user():
    f = Faker('ru_RU')
    p = f.profile()
    User.objects.create(
        username=p['username'],
        email=p['mail'],
        password=make_password(f.password(length=8)),
    )


@app.task(ignore_result=True)
def fake_post(user_id):
    f = Faker('ru_RU')
    Post.objects.create(
        title=f.sentence(nb_words=5),
        content=f.sentence(nb_words=500),
        date=f.date_time_between(),
        user_id=user_id
    )
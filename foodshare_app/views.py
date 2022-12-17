import datetime

from celery import group, chain, chord
from celery.result import AsyncResult
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseNotAllowed, HttpResponseNotFound
from django.shortcuts import render, redirect, HttpResponse
from django.views.decorators.cache import cache_page
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from foodshare_app import models
from .forms import PostModelForm
from .paginator import CachedPaginator
from .tasks import add, factorial, ssum, xsum, fake_post, fake_user

User = get_user_model()


def task(request):
    if request.GET.get('opt') == 'fact':
        res = factorial.apply_async([request.GET.get('n')], {})

    elif request.GET.get('opt') == 'ssum':
        res = ssum.delay(request.GET.get('n'))

    elif request.GET.get('opt') == 'gr':
        n = int(request.GET.get('n'))

        s = factorial.s(n)
        print(s)

        res = group(factorial.s(i) for i in range(n)).delay()

    elif request.GET.get('opt') == 'ch':
        n = int(request.GET.get('n'))  # 10

        res = chain(
            factorial.s(n), add.s(n), add.s(n+n)
        ).delay()

    elif request.GET.get('opt') == 'chord':
        n = int(request.GET.get('n'))  # 10

        res = chord(
            [factorial.s(n), factorial.s(n+n)], xsum.s()
        )()

    else:
        x = request.GET.get('x')
        y = request.GET.get('y')
        res = add.delay(x, y)
    return HttpResponse(res)


def get_task(request, uuid: str):
    result = AsyncResult(uuid)
    s = f'{result}<br>{result.status}<br>{result.result}'
    result.forget()
    return HttpResponse(s)


def fake_create_user(request):
    for _ in range(100):
        fake_user.delay()
    return redirect('/')


def fake_create_posts(request):
    for u in User.objects.all():
        for _ in range(1000):
            fake_post.delay(u.id)
    return redirect('/')


def profile(request, user_name):
    try:
        p = int(request.GET.get('p', 1))
    except ValueError:
        p = 1

    try:
        print(user_name, models.Profile.objects.all())
        user_profile = models.Profile.objects.get(user__username=user_name)
        print(user_profile)
        posts = models.Post.objects.filter(user__username=user_name).order_by('-date')
        print(posts)
        pages = Paginator(posts, 100)
        return render(
            request,
            'registration/profile.html',
            {
                'profile': user_profile,
                'posts': pages.page(p),
                'page': p,
                'num_pages': int(pages.num_pages)
            }
        )

    except (User.DoesNotExist, models.Profile.DoesNotExist):
        return redirect('home')


def delete(request, post_id):
    if request.method == 'POST':
        try:
            models.Post.objects.get(id=post_id).delete()
            return redirect('/posts/')
        except models.Post.DoesNotExist:
            return HttpResponseNotFound(request)
    else:
        return HttpResponseNotAllowed(request)


@cache_page(60 * 10)
def post(request, post_id):
    try:
        user_post = models.Post.objects.get(id=post_id)
        author = user_post.user.username
        print(user_post.image)
        return render(request, 'posts/user_post.html', {'post': user_post, 'user': author})
    except models.Post.DoesNotExist:
        return HttpResponseNotFound(request)


class PostCreateView(LoginRequiredMixin, CreateView):
    model = models.Post
    form_class = PostModelForm
    template_name = 'posts/create_2.html'

    def form_valid(self, form):
        r = super().form_valid(form)
        self.object.user = self.request.user
        self.object.save()
        return r


class PostUpdateView(UserPassesTestMixin, UpdateView):
    model = models.Post
    form_class = PostModelForm
    success_url = '/posts/{id}'
    template_name = 'posts/update.html'
    permission_denied_message = 'Нет доступа к редактированию данного поста!'

    def test_func(self):
        pk = self.kwargs.get(self.pk_url_kwarg)
        post_user_id = models.Post.objects.filter(id=pk).values('user_id').first()['user_id']
        return self.request.user.id == post_user_id


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = models.Post
    success_url = '/'


class PostShowView(ListView):
    model = models.Post
    paginate_by = 100
    template_name = 'posts/posts.html'
    context_object_name = 'posts'
    ordering = ('-date',)
    page_kwarg = 'p'

    def get_paginator(self, queryset, per_page, orphans=0, allow_empty_first_page=True, **kwargs):
        # Имя для кеша
        cache_name = f'{self.model.__name__}{self.request.GET.get("d", "")}{self.request.GET.get("s", "")}'
        # Возвращаем paginator
        return CachedPaginator(queryset, per_page, orphans, allow_empty_first_page, cache_name)

    def get_queryset(self):
        if self.request.GET.get('d'):
            date = datetime.datetime.strptime(self.request.GET['d'], '%Y-%m-%d')
            date_to = date + datetime.timedelta(days=1)
            date_query = (Q(date__gte=date) & Q(date__lt=date_to))
        else:
            date_query = Q()

        if self.request.GET.get('s'):
            s = self.request.GET['s']
            q1 = models.Post.objects.filter(
                date_query & Q(title__contains=s) & ~Q(content__contains=s)
            ).order_by('-date')
            q2 = models.Post.objects.filter(
                date_query & ~Q(title__contains=s) & Q(content__contains=s)
            ).order_by('-date')

            q = q1 | q2

        else:
            q = models.Post.objects.filter(date_query).order_by('-date').all().values('id', 'title', 'user', 'date')
            print(q.query)
        return q



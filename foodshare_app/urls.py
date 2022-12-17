from django.urls import path
from foodshare_app import views as posts_views

# POSTS
# /posts/

urlpatterns = [
    path('task/', posts_views.task),
    path('task/<uuid>', posts_views.get_task),

    path('', posts_views.PostShowView.as_view(), name='show_posts'),

    path('create', posts_views.PostCreateView.as_view(), name='create_post'),

    path('update/<int:pk>', posts_views.PostUpdateView.as_view(), name='update'),

    path('delete/<int:pk>', posts_views.PostDeleteView.as_view(), name='delete'),

    path('<int:post_id>', posts_views.post, name='get_post'),

    path('profile/<user_name>', posts_views.profile, name='profile'),

    # FAKE
    path('fake/users', posts_views.fake_create_user),
    path('fake/posts', posts_views.fake_create_posts),
]

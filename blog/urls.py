"""URL map for the blog app.

`app_name` turns every name below into `blog:<name>`, which is what
`{% url 'blog:post_detail' %}` and `reverse()` look up. Namespacing means the
project can grow a second app with its own `home` without a collision.

Order matters: Django takes the *first* pattern that matches. `post/new/`
has to come before `post/<slug:slug>/`, or "new" would be read as a slug and
you would get a 404 on the create page.
"""

from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.index, name='home'),
    path('posts/', views.post_list, name='post_list'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('about/', views.about, name='about'),

    path('section/<slug:slug>/', views.category_detail, name='category_detail'),

    path('post/new/', views.post_create, name='post_create'),
    path('post/<slug:slug>/', views.post_detail, name='post_detail'),
    path('post/<slug:slug>/edit/', views.post_edit, name='post_edit'),
    path('post/<slug:slug>/delete/', views.post_delete, name='post_delete'),
    path('post/<slug:slug>/publish/', views.post_publish, name='post_publish'),

    path('comment/<int:pk>/delete/', views.comment_delete, name='comment_delete'),
    path('comment/<int:pk>/toggle/', views.comment_toggle, name='comment_toggle'),
]

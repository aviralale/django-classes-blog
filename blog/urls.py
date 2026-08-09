from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.index, name="home"),
    path('posts/', views.post_list, name="post_list"),
    path('post/new/', views.post_create, name='post_create'),
    path('post/<slug:slug>/', views.post_detail, name="post_detail"),
    path('post/<slug:slug>/edit/', views.post_edit, name="post_edit"),
    path('about/', views.about, name="about"),
]
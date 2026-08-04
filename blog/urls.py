from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('post/<slug:slug>/', views.post_detail),
    path('about/', views.about),
]
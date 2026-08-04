from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import Post

# Create your views here.
# def index(request):
#     return HttpResponse("<h1>Hello my name is aviral</h1>")

def index(request):
    posts = Post.objects.all()
    return render(request, 'blog/home.html', {'posts': posts})

def post_detail(request, slug):
    # post = Post.objects.get(slug=slug)
    post = get_object_or_404(Post, slug=slug)
    return render(request, 'blog/post_detail.html', {'post': post})

def about(request):
    return HttpResponse("<h1>I stu`d`y at Texas</h1>")
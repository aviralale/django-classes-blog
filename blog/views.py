from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import Post, Category, Comment

# Create your views here.
# def index(request):
#     return HttpResponse("<h1>Hello my name is aviral</h1>")

def index(request):
    posts = Post.objects.all()
    categories = Category.objects.all()
    return render(request, 'blog/home.html', {
        'posts': posts, 
        'categories': categories
    })

def post_detail(request, slug):
    # post = Post.objects.get(slug=slug)
    post = get_object_or_404(Post, slug=slug)
    errors = []
    name = ''
    content = ''

    if request.method == 'POST':
        name = request.POST.get('name', '')
        content = request.POST.get('content', '')

        if not name:
            errors.append('Name is required!')
        
        elif len(name) >= 100:
            errors.append('Name is too long.')
        
        if not content:
            errors.append('Content is required!')
        
        if not errors:
            Comment.objects.create(post=post, name=name, content=content)
            redirect('blog:post_detail', slug=post.slug)

    return render(request, 'blog/post_detail.html', 
    {
        'post': post,
        'errors': errors,
        'name': name,
        'content': content
        })

def about(request):
    return HttpResponse("<h1>I study at Texas</h1>")
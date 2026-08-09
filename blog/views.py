from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q
from .models import Post, Category
from .forms import CommentForm, PostForm
from django.contrib.auth.decorators import login_required, permission_required


# Create your views here.
# def index(request):
#     return HttpResponse("<h1>Hello my name is aviral</h1>")

def index(request):
    posts = Post.objects.select_related('category')
    categories = Category.objects.annotate(post_count=Count('post')).filter(post_count__gt=0)
    lead = posts.first()
    return render(request, 'blog/home.html', {
        'lead': lead,
        'posts': posts[1:],
        'categories': categories,
        'total': posts.count(),
    })

def post_detail(request, slug):
    # post = Post.objects.get(slug=slug)
    post = get_object_or_404(Post.objects.select_related('category'), slug=slug)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.save()
            return redirect('blog:post_detail', slug=post.slug)
    else:
        form = CommentForm()

    related = Post.objects.filter(category=post.category).exclude(pk=post.pk)[:3]

    return render(request, 'blog/post_detail.html', {
        'post': post,
        'form': form,
        'comments': post.comments.all(),
        'related': related,
    })

@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            form.save()
            return redirect('blog:post_detail', slug=post.slug)
    else:
        form = PostForm()
    return render(request, 'blog/post_create.html', {'form': form})


@login_required
@permission_required('blog.change_post', raise_exception=True)
def post_edit(request, slug):
    post = get_object_or_404(Post, slug=slug)

    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post)

        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', slug=post.slug)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/post_edit.html', {
        'form': form,
        'post': post,
        'heading': "Edit Post",
    })

def about(request):
    return render(request, 'blog/about.html', {
        'total': Post.objects.count(),
        'categories': Category.objects.annotate(post_count=Count('post')).filter(post_count__gt=0),
    })

def post_list(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')

    posts = Post.objects.select_related('category')
    if query:
        posts = posts.filter(Q(title__icontains=query) | Q(content__icontains=query))

    active_category = None
    if category_id.isdigit():
        active_category = Category.objects.filter(pk=category_id).first()
        if active_category:
            posts = posts.filter(category=active_category)

    context = {
        'posts': posts,
        'query': query,
        'categories': Category.objects.annotate(post_count=Count('post')).filter(post_count__gt=0),
        'active_category': active_category,
    }
    return render(request, 'blog/post_list.html', context)

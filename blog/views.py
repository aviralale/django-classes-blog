"""Views.

A view is a function that takes a request and returns a response. Everything
else — the ORM, the templates, the forms — is a helper it calls on the way.

Three rules run through this file:

  * **Drafts are private.** Public pages read `Post.published`. Pages that may
    show a draft read `Post.objects.visible_to(request.user)`, and a draft you
    are not allowed to see returns 404, not 403 — a 403 would confirm that the
    post exists.
  * **Commenting requires an account.** The form has no name field; the author
    is `request.user`, which the browser cannot forge.
  * **Permissions gate the verb, ownership gates the row.** `blog.change_post`
    says you may edit posts at all; `post.is_editable_by(user)` says whether
    you may edit *this* one.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import CommentForm, PostForm
from .models import Category, Comment, Post

PAGE_SIZE = 9


def sections():
    """Categories that actually have something published in them.

    `filter=` inside Count is a conditional aggregate: one query, counting
    only the rows that match, instead of counting everything and filtering in
    Python.
    """
    return Category.objects.annotate(
        post_count=Count(
            'posts',
            filter=Q(
                posts__status=Post.Status.PUBLISHED,
                posts__published_at__lte=timezone.now(),
            ),
        )
    ).filter(post_count__gt=0)


def paginate(request, queryset, per_page=PAGE_SIZE):
    """Slice a queryset into pages and hand back the current one.

    Paginator only ever pulls one page out of the database — `page.object_list`
    is a LIMIT/OFFSET query, not the whole table.
    """
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get('page'))


# --- reading -----------------------------------------------------------

def index(request):
    posts = list(Post.published.with_related()[:7])
    lead, rest = (posts[0], posts[1:]) if posts else (None, [])
    return render(request, 'blog/home.html', {
        'lead': lead,
        'posts': rest,
        'categories': sections(),
        'total': Post.published.count(),
    })


def post_list(request):
    query = request.GET.get('q', '').strip()
    slug = request.GET.get('category', '').strip()

    posts = Post.published.with_related().search(query)

    active_category = None
    if slug:
        active_category = Category.objects.filter(slug=slug).first()
        if active_category is None and slug.isdigit():
            # Older links used ?category=<pk>. Keep them working.
            active_category = Category.objects.filter(pk=slug).first()
        if active_category:
            posts = posts.filter(category=active_category)

    page = paginate(request, posts)
    return render(request, 'blog/post_list.html', {
        'page': page,
        'posts': page.object_list,
        'query': query,
        'categories': sections(),
        'active_category': active_category,
        'total': page.paginator.count,
    })


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    page = paginate(request, Post.published.with_related().filter(category=category))
    return render(request, 'blog/category_detail.html', {
        'category': category,
        'page': page,
        'posts': page.object_list,
        'total': page.paginator.count,
    })


def post_detail(request, slug):
    # `visible_to` keeps drafts out of everyone else's hands, and the 404 from
    # get_object_or_404 does not distinguish "no such post" from "not yours".
    post = get_object_or_404(
        Post.objects.with_related().visible_to(request.user), slug=slug
    )

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.info(request, 'Log in to leave a comment.')
            return redirect_to_login(request.get_full_path())

        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)   # build it, do not hit the DB yet
            comment.post = post                 # fill in what the form cannot
            comment.author = request.user
            comment.save()
            messages.success(request, 'Comment posted.')
            # Redirect after POST so a refresh does not post it twice.
            return redirect(f'{post.get_absolute_url()}#comments')
    else:
        form = CommentForm()

    related = Post.published.with_related().filter(category=post.category).exclude(pk=post.pk)[:3]

    return render(request, 'blog/post_detail.html', {
        'post': post,
        'form': form,
        'comments': post.comments.select_related('author').visible_to(request.user),
        'related': related,
        'can_edit': post.is_editable_by(request.user),
        'can_delete': post.is_deletable_by(request.user),
    })


def about(request):
    return render(request, 'blog/about.html', {
        'total': Post.published.count(),
        'categories': sections(),
    })


# --- writing -----------------------------------------------------------

@login_required
@permission_required('blog.add_post', raise_exception=True)
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(
                request,
                'Published.' if post.is_published else 'Saved as a draft. Only you can see it.',
            )
            return redirect(post)
    else:
        form = PostForm()
    return render(request, 'blog/post_form.html', {
        'form': form,
        'heading': 'Write something worth printing',
        'kicker': 'The desk',
        'dek': 'Long paragraphs are fine. Blank lines make new ones.',
        'submit_label': 'Save',
    })


@login_required
def post_edit(request, slug):
    post = get_object_or_404(Post.objects.visible_to(request.user), slug=slug)
    if not post.is_editable_by(request.user):
        # A 403 is right here: you already know the post exists, you just
        # cannot touch it.
        raise PermissionDenied('This is not your post.')

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Changes saved.')
            return redirect(post)
    else:
        form = PostForm(instance=post)

    return render(request, 'blog/post_form.html', {
        'form': form,
        'post': post,
        'heading': 'Edit post',
        'kicker': 'The desk',
        'dek': 'Fix the typo before anyone notices.',
        'submit_label': 'Update',
    })


@login_required
def post_delete(request, slug):
    post = get_object_or_404(Post.objects.visible_to(request.user), slug=slug)
    if not post.is_deletable_by(request.user):
        raise PermissionDenied('This is not your post.')

    if request.method == 'POST':
        title = post.title
        post.delete()
        messages.warning(request, f'"{title}" is gone.')
        return redirect('blog:dashboard')

    # GET just asks. Never delete anything on a GET — a link prefetcher,
    # a crawler or a browser preview will happily "click" it for you.
    return render(request, 'blog/post_confirm_delete.html', {'post': post})


@login_required
@require_POST
def post_publish(request, slug):
    """Flip a post between draft and published.

    POST only, so it needs the CSRF token and cannot be triggered by an
    <img src> on someone else's site.
    """
    post = get_object_or_404(Post.objects.visible_to(request.user), slug=slug)
    if not post.is_editable_by(request.user):
        raise PermissionDenied('This is not your post.')

    post.status = Post.Status.DRAFT if post.is_published else Post.Status.PUBLISHED
    post.save()
    messages.success(
        request,
        'Published — it is on the front page now.' if post.is_published
        else 'Pulled back to draft.',
    )
    return redirect(request.POST.get('next') or post.get_absolute_url())


@login_required
def dashboard(request):
    """Your desk: your own pieces, drafts included."""
    mine = (
        Post.objects.filter(author=request.user)
        .with_related()
        .annotate(comment_count=Count('comments'))
    )

    context = {
        'posts': mine,
        'draft_count': mine.filter(status=Post.Status.DRAFT).count(),
        'published_count': mine.filter(status=Post.Status.PUBLISHED).count(),
    }

    # Editors get a second table: everyone else's unpublished work.
    if request.user.has_perm('blog.can_publish_post'):
        context['review_queue'] = (
            Post.objects.drafts().with_related().exclude(author=request.user)
        )
    if request.user.has_perm('blog.can_moderate_comment'):
        context['hidden_comments'] = (
            Comment.objects.filter(is_approved=False).select_related('post', 'author')
        )

    return render(request, 'blog/dashboard.html', context)


# --- moderating --------------------------------------------------------

@login_required
@require_POST
def comment_delete(request, pk):
    comment = get_object_or_404(Comment.objects.select_related('post'), pk=pk)
    if not comment.is_deletable_by(request.user):
        raise PermissionDenied('Not your comment.')
    url = comment.post.get_absolute_url()
    comment.delete()
    messages.warning(request, 'Comment deleted.')
    return redirect(f'{url}#comments')


@login_required
@permission_required('blog.can_moderate_comment', raise_exception=True)
@require_POST
def comment_toggle(request, pk):
    comment = get_object_or_404(Comment.objects.select_related('post'), pk=pk)
    comment.is_approved = not comment.is_approved
    comment.save(update_fields=['is_approved', 'updated_at'])
    messages.success(
        request, 'Comment restored.' if comment.is_approved else 'Comment hidden.'
    )
    return redirect(request.POST.get('next') or f'{comment.post.get_absolute_url()}#comments')

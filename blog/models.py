"""The data layer for the blog.

Three tables, two relationships and one rule that matters:

    Category  1 ── * Post  * ── 1 User        (a post has a section and an author)
    Post      1 ── * Comment * ── 1 User      (a comment belongs to a post and a user)

A Post is either a *draft* (only its author and the editors can see it) or
*published* (everyone can). Every query on the public side of the site goes
through `Post.published`, so there is exactly one place where that rule lives.
"""

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import Truncator, slugify


def unique_slug(model, value, instance=None, field='slug'):
    """Turn `value` into a slug nothing else in `model` is using yet.

    'My Country Nepal' -> 'my-country-nepal', and if that is taken,
    'my-country-nepal-1', '-2', and so on. `instance` is excluded from the
    check so re-saving a row does not collide with itself.
    """
    base = slugify(value) or 'post'
    slug = base
    counter = 1
    taken = model._default_manager.all()
    if instance is not None and instance.pk:
        taken = taken.exclude(pk=instance.pk)
    while taken.filter(**{field: slug}).exists():
        slug = f'{base}-{counter}'
        counter += 1
    return slug


class Category(models.Model):
    """A section of the magazine: Django, The Web, Engineering, Tooling."""

    name = models.CharField(max_length=54, unique=True)
    slug = models.SlugField(max_length=64, unique=True, blank=True)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Category, self.name, instance=self)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:category_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.name


class PostQuerySet(models.QuerySet):
    """Reusable filters.

    Because these live on the queryset (not the view) they chain:

        Post.objects.published().in_category(cat).search('django')
    """

    def published(self):
        return self.filter(
            status=Post.Status.PUBLISHED,
            published_at__lte=timezone.now(),
        )

    def drafts(self):
        return self.filter(status=Post.Status.DRAFT)

    def with_related(self):
        """One JOIN instead of one query per row — see the N+1 article."""
        return self.select_related('category', 'author')

    def search(self, term):
        if not term:
            return self
        return self.filter(
            models.Q(title__icontains=term) | models.Q(content__icontains=term)
        )

    def visible_to(self, user):
        """Everything public, plus the drafts this particular user may read.

        Editors (anyone holding `blog.can_publish_post`) see every draft.
        Ordinary authors see only their own.
        """
        if user.is_authenticated:
            if user.is_superuser or user.has_perm('blog.can_publish_post'):
                return self
            return self.filter(
                models.Q(status=Post.Status.PUBLISHED, published_at__lte=timezone.now())
                | models.Q(author=user)
            )
        return self.published()


class PublishedManager(models.Manager.from_queryset(PostQuerySet)):
    """`Post.published` — the public site's front door.

    `from_queryset` copies every method of PostQuerySet onto the manager, so
    `Post.published.with_related()` works. A plain `models.Manager` subclass
    would only give you the handful of built-in methods.
    """

    def get_queryset(self):
        return super().get_queryset().published()


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    content = models.TextField()
    featured_image = models.ImageField(
        upload_to='blog_images/', default='blog_images/default.png'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts'
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts'
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.DRAFT
    )
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # The first manager declared is the default one, the one the admin and
    # every reverse relation use. Keep `objects` first and unfiltered.
    objects = PostQuerySet.as_manager()
    published = PublishedManager()

    class Meta:
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['-published_at'], name='post_published_at_idx'),
            models.Index(fields=['status', '-published_at'], name='post_status_pub_idx'),
        ]
        permissions = [
            ('can_publish_post', 'Can publish or unpublish any post'),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Post, self.title, instance=self)
        # Stamp the publication date the first time it goes live, and clear it
        # again if it is pulled back to draft.
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        if self.status == self.Status.DRAFT:
            self.published_at = None
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.title

    # --- derived values the templates use ------------------------------

    @property
    def is_published(self):
        return self.status == self.Status.PUBLISHED

    @property
    def excerpt(self):
        """First slice of the article, used on the cards."""
        return Truncator(self.content).chars(190)

    @property
    def reading_time(self):
        """Minutes, at a lazy 200 words per minute."""
        words = len(self.content.split())
        return max(1, round(words / 200))

    # --- who is allowed to do what -------------------------------------
    #
    # Django's permissions are per *model*: "can change posts", not "can
    # change this post". Ownership is the missing half, so the rule lives
    # on the model where the views and the templates can both ask it.

    def is_editable_by(self, user):
        if not user.is_authenticated:
            return False
        if user.is_superuser or user.has_perm('blog.can_publish_post'):
            return True
        return self.author_id == user.pk and user.has_perm('blog.change_post')

    def is_deletable_by(self, user):
        if not user.is_authenticated:
            return False
        if user.is_superuser or user.has_perm('blog.can_publish_post'):
            return True
        return self.author_id == user.pk and user.has_perm('blog.delete_post')

    def is_visible_to(self, user):
        if self.is_published:
            return True
        if not user.is_authenticated:
            return False
        return (
            user.is_superuser
            or user.has_perm('blog.can_publish_post')
            or self.author_id == user.pk
        )


class CommentQuerySet(models.QuerySet):
    def visible_to(self, user):
        """Approved comments, plus your own while they are hidden."""
        if user.is_authenticated:
            if user.is_superuser or user.has_perm('blog.can_moderate_comment'):
                return self
            return self.filter(models.Q(is_approved=True) | models.Q(author=user))
        return self.filter(is_approved=True)


class Comment(models.Model):
    """A signed comment. Anonymous comments are not a thing here — you log in
    or you read quietly."""

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments'
    )
    content = models.TextField()
    is_approved = models.BooleanField(
        default=True,
        help_text='Untick to hide the comment from everyone except its author.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CommentQuerySet.as_manager()

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'created_at'], name='comment_post_created_idx')
        ]
        permissions = [
            ('can_moderate_comment', 'Can hide or delete anyone\'s comment'),
        ]

    def __str__(self):
        return f'Comment by {self.author} on {self.post.title}'

    def is_deletable_by(self, user):
        if not user.is_authenticated:
            return False
        return (
            user.is_superuser
            or user.has_perm('blog.can_moderate_comment')
            or self.author_id == user.pk
        )

    def is_visible_to(self, user):
        if self.is_approved:
            return True
        if not user.is_authenticated:
            return False
        return (
            user.is_superuser
            or user.has_perm('blog.can_moderate_comment')
            or self.author_id == user.pk
        )

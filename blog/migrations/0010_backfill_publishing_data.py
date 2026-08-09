"""Step 2 of 3: fill the new columns in.

A *data* migration. It contains no schema changes at all — it only moves
values around, using `apps.get_model()` to get the version of each model as
it looked at this point in history. Never import your real models here: this
file has to keep working after you rename a field two years from now.

What it does:
  1. merges categories that share a name (0011 makes the name unique)
  2. gives every category a slug
  3. marks every pre-existing post as published, since drafts did not exist
     when they were written
  4. finds an owner for any post that somehow has none
  5. converts each comment's typed-in `name` into a real user account
"""

from django.conf import settings
from django.db import migrations
from django.utils.text import slugify


def _unique(taken, base, limit):
    """`base`, or `base-1`, `base-2`... — whatever `taken` does not hold."""
    base = base[:limit] or 'item'
    candidate = base
    counter = 1
    while candidate in taken:
        suffix = f'-{counter}'
        candidate = base[: limit - len(suffix)] + suffix
        counter += 1
    taken.add(candidate)
    return candidate


def forwards(apps, schema_editor):
    Category = apps.get_model('blog', 'Category')
    Post = apps.get_model('blog', 'Post')
    Comment = apps.get_model('blog', 'Comment')
    User = apps.get_model(settings.AUTH_USER_MODEL)

    # 1 + 2. one category per name, each with a slug
    seen_names = {}
    slugs = set()
    for category in Category.objects.order_by('pk'):
        keeper = seen_names.get(category.name.lower())
        if keeper is not None:
            Post.objects.filter(category=category).update(category=keeper)
            category.delete()
            continue
        seen_names[category.name.lower()] = category
        category.slug = _unique(slugs, slugify(category.name), 64)
        category.save(update_fields=['slug'])

    # 4. a post has to belong to someone. Prefer a superuser, then any user,
    #    and only invent an account if the table is genuinely empty.
    fallback = None
    if Post.objects.filter(author__isnull=True).exists() or Comment.objects.exists():
        fallback = (
            User.objects.filter(is_superuser=True).order_by('pk').first()
            or User.objects.order_by('pk').first()
        )
        if fallback is None:
            fallback = User.objects.create(
                username='archive',
                email='',
                password='!',  # unusable: nobody can log in as this account
                is_active=False,
            )
    Post.objects.filter(author__isnull=True).update(author=fallback)

    # 3. everything that existed before this migration was already live
    Post.objects.update(status='published')
    for post in Post.objects.all():
        Post.objects.filter(pk=post.pk).update(published_at=post.created_at)

    # 5. comments were signed with a free-text name. Turn each distinct name
    #    into an inactive account so the FK in 0011 has something to point at.
    usernames = set(User.objects.values_list('username', flat=True))
    by_name = {}
    for comment in Comment.objects.filter(author__isnull=True):
        raw = (comment.name or '').strip()
        if not raw:
            comment.author = fallback
            comment.save(update_fields=['author'])
            continue

        user = by_name.get(raw.lower())
        if user is None:
            username = _unique(usernames, slugify(raw).replace('-', '_'), 150)
            user = User.objects.create(
                username=username,
                email='',
                password='!',
                is_active=False,
            )
            by_name[raw.lower()] = user
        comment.author = user
        comment.save(update_fields=['author'])


def backwards(apps, schema_editor):
    """There is nothing to undo — the old columns are still there and the new
    ones are about to be dropped by the reverse of 0009."""


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0009_publishing_and_signed_comments'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]

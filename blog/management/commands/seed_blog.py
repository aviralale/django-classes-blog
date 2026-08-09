"""Fill the blog with real articles, printed covers and a few comments.

    python manage.py seed_blog            # publish anything missing
    python manage.py seed_blog --reset    # republish the seeded articles
    python manage.py seed_blog --purge    # also delete every other post

Only the articles listed in blog/seed_data.py are ever touched, unless you
explicitly ask for --purge.
"""

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from blog.covers import make_cover
from blog.models import Category, Comment, Post
from blog.seed_data import ARTICLES, COMMENTS

COVER_DIR = 'blog_images/covers'


class Command(BaseCommand):
    help = 'Publish a set of real articles with generated covers and comments.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete and rewrite the seeded articles (and their comments).',
        )
        parser.add_argument(
            '--purge',
            action='store_true',
            help='Danger: delete every post in the database first, seeded or not.',
        )

    def handle(self, *args, **options):
        slugs = [slugify(article['title']) for article in ARTICLES]

        if options['purge']:
            deleted, _ = Post.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Purged all posts ({deleted} rows).'))
        elif options['reset']:
            Post.objects.filter(slug__in=slugs).delete()
            self.stdout.write(self.style.WARNING('Removed the previously seeded articles.'))

        covers = settings.MEDIA_ROOT / COVER_DIR
        covers.mkdir(parents=True, exist_ok=True)

        now = timezone.now()
        published = 0

        for article in ARTICLES:
            slug = slugify(article['title'])
            if Post.objects.filter(slug=slug).exists():
                self.stdout.write(f'  skip   {slug}')
                continue

            category, _ = Category.objects.get_or_create(name=article['category'])

            # JPEG, not PNG: the paper grain is noise, and noise makes PNG enormous
            cover_path = covers / f'{slug}.jpg'
            make_cover(slug).save(cover_path, 'JPEG', quality=86, optimize=True, progressive=True)

            post = Post.objects.create(
                title=article['title'],
                content=article['content'],
                author=article['author'],
                category=category,
                slug=slug,
                featured_image=f'{COVER_DIR}/{slug}.jpg',
            )

            # created_at is auto_now_add, so it has to be corrected afterwards
            written_at = now - timedelta(days=article['days_ago'], hours=article['days_ago'] % 7)
            Post.objects.filter(pk=post.pk).update(created_at=written_at)

            for name, body, days_ago in COMMENTS.get(slug, []):
                comment = Comment.objects.create(post=post, name=name, content=body)
                Comment.objects.filter(pk=comment.pk).update(
                    created_at=written_at + timedelta(days=article['days_ago'] - days_ago, hours=3)
                )

            published += 1
            self.stdout.write(self.style.SUCCESS(f'  publish {slug}'))

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone. {published} new article(s), {Post.objects.count()} on the site.'
            )
        )

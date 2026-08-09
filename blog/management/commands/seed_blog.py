"""Fill an empty database with a working magazine.

    python manage.py seed_blog            # add anything missing
    python manage.py seed_blog --reset    # rewrite the seeded articles
    python manage.py seed_blog --purge    # delete every post first, then seed

It creates the groups, the accounts, the sections, the articles (one of them a
draft), the generated cover plates and the comments. Everything it writes comes
from blog/seed_data.py; the only articles it ever touches are the ones listed
there, unless you explicitly ask for --purge.

A management command is just a class with a `handle()` method in
`<app>/management/commands/<name>.py`. Django finds it by directory layout —
there is nothing to register — and `self.stdout.write` rather than `print` so
that `call_command(..., stdout=...)` can capture the output in a test.
"""

from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from blog.covers import make_cover
from blog.models import Category, Comment, Post
from blog.seed_data import ARTICLES, COMMENTS, DEMO_PASSWORD, PEOPLE, SECTIONS

User = get_user_model()

COVER_DIR = 'blog_images/covers'


class Command(BaseCommand):
    help = 'Publish a set of real articles with generated covers, accounts and comments.'

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
        parser.add_argument(
            '--skip-users',
            action='store_true',
            help='Do not create the demo accounts. Posts are attributed to the first superuser.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        slugs = [slugify(article['title']) for article in ARTICLES]

        if options['purge']:
            deleted, _ = Post.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Purged all posts ({deleted} rows).'))
        elif options['reset']:
            Post.objects.filter(slug__in=slugs).delete()
            self.stdout.write(self.style.WARNING('Removed the previously seeded articles.'))

        # The groups have to exist before anyone can be put in one.
        call_command('sync_roles', verbosity=0)

        people = self.seed_people(skip=options['skip_users'])
        self.seed_sections()
        self.seed_articles(people)

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone. {Post.published.count()} published, '
                f'{Post.objects.drafts().count()} draft(s), '
                f'{Comment.objects.count()} comment(s).'
            )
        )
        if not options['skip_users']:
            self.stdout.write(f'Demo accounts all use the password: {DEMO_PASSWORD}')
            self.stdout.write('Try `aviral` (Editor) against `sanjay.k` (Reader) to see permissions bite.')

    # --- accounts -------------------------------------------------------

    def seed_people(self, skip=False):
        """Return {username: User}. Existing accounts keep their password."""
        if skip:
            fallback = User.objects.filter(is_superuser=True).first() or User.objects.first()
            if fallback is None:
                raise SystemExit('No users exist. Run createsuperuser, or drop --skip-users.')
            return {person['username']: fallback for person in PEOPLE}

        people = {}
        for person in PEOPLE:
            user, created = User.objects.get_or_create(
                username=person['username'],
                defaults={
                    'first_name': person['first_name'],
                    'last_name': person['last_name'],
                    'email': f"{person['username'].replace('.', '')}@example.com",
                },
            )
            if created:
                # set_password hashes it. Never assign to user.password directly.
                user.set_password(DEMO_PASSWORD)
                user.save(update_fields=['password'])

            group = Group.objects.filter(name=person['role']).first()
            if group:
                # A signal already put new accounts in the default group, so
                # clear it first — otherwise a Reader would keep Author rights.
                user.groups.set([group])

            people[person['username']] = user
            self.stdout.write(
                f"  {'account' if created else 'exists ':8} {person['username']:16} {person['role']}"
            )
        return people

    # --- sections -------------------------------------------------------

    def seed_sections(self):
        for name, description in SECTIONS.items():
            Category.objects.update_or_create(
                name=name, defaults={'description': description}
            )

    # --- articles -------------------------------------------------------

    def seed_articles(self, people):
        covers = settings.MEDIA_ROOT / COVER_DIR
        covers.mkdir(parents=True, exist_ok=True)

        now = timezone.now()
        published = 0

        for article in ARTICLES:
            slug = slugify(article['title'])
            if Post.objects.filter(slug=slug).exists():
                self.stdout.write(f'  skip     {slug}')
                continue

            category, _ = Category.objects.get_or_create(name=article['category'])
            author = people[article['author']]

            # JPEG, not PNG: the paper grain is noise, and noise makes PNG enormous
            cover_path = covers / f'{slug}.jpg'
            make_cover(slug).save(cover_path, 'JPEG', quality=86, optimize=True, progressive=True)

            written_at = now - timedelta(
                days=article['days_ago'], hours=article['days_ago'] % 7
            )

            post = Post.objects.create(
                title=article['title'],
                content=article['content'],
                author=author,
                category=category,
                slug=slug,
                status=article['status'],
                featured_image=f'{COVER_DIR}/{slug}.jpg',
            )

            # created_at is auto_now_add, so it can only be corrected afterwards
            # — and .update() skips save(), which is what we want here.
            Post.objects.filter(pk=post.pk).update(
                created_at=written_at,
                published_at=written_at if post.is_published else None,
            )

            for username, body, days_ago in COMMENTS.get(slug, []):
                comment = Comment.objects.create(
                    post=post, author=people[username], content=body
                )
                Comment.objects.filter(pk=comment.pk).update(
                    created_at=written_at
                    + timedelta(days=article['days_ago'] - days_ago, hours=3)
                )

            published += 1
            label = 'publish ' if post.is_published else 'draft   '
            self.stdout.write(self.style.SUCCESS(f'  {label} {slug}'))

        self.stdout.write(f'\n{published} new article(s) written.')

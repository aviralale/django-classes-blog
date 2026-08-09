"""Tests for the rules this project invented.

Nothing here asserts that Django works. There is no test that saving a model
stores a string, or that a ForeignKey points at a row — that code belongs to
Django and is already tested by Django. What is tested here is every sentence
we would say out loud about how the site behaves:

    a draft is invisible to everyone except its author and the editors
    you cannot comment without an account
    an author may edit their own post and nobody else's
    publishing stamps the date once and does not move it afterwards

Run them with:  python manage.py test
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.template import Context, Template
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import CommentForm, PostForm
from .models import Category, Comment, Post

User = get_user_model()


class BlogTestCase(TestCase):
    """Shared cast.

    `setUpTestData` runs once for the whole class inside a transaction that is
    rolled back afterwards, instead of once per test method like `setUp`. On a
    suite this size it is the difference between seconds and tens of seconds.
    """

    @classmethod
    def setUpTestData(cls):
        call_command('sync_roles', verbosity=0)

        cls.section = Category.objects.create(name='Django')

        cls.author = cls.make_user('author', 'Authors')
        cls.other_author = cls.make_user('other', 'Authors')
        cls.editor = cls.make_user('editor', 'Editors')
        cls.reader = cls.make_user('reader', 'Readers')

        cls.post = Post.objects.create(
            title='A published piece',
            content='word ' * 60,
            author=cls.author,
            category=cls.section,
            status=Post.Status.PUBLISHED,
        )
        cls.draft = Post.objects.create(
            title='A quiet draft',
            content='word ' * 60,
            author=cls.author,
            category=cls.section,
            status=Post.Status.DRAFT,
        )

    @staticmethod
    def make_user(username, role):
        user = User.objects.create_user(username=username, password='testpass123')
        # A post_save signal already put them in the default group, so `set`
        # rather than `add` — otherwise a Reader keeps Author permissions.
        user.groups.set([Group.objects.get(name=role)])
        return user


class SlugTests(BlogTestCase):
    def test_slug_is_generated_from_the_title(self):
        post = Post.objects.create(title='My Country Nepal', content='x', author=self.author)
        self.assertEqual(post.slug, 'my-country-nepal')

    def test_duplicate_titles_get_a_numbered_slug(self):
        first = Post.objects.create(title='Same Title', content='x', author=self.author)
        second = Post.objects.create(title='Same Title', content='x', author=self.author)
        self.assertEqual(first.slug, 'same-title')
        self.assertEqual(second.slug, 'same-title-1')

    def test_resaving_a_post_keeps_its_slug(self):
        """The URL of a published article is a promise. Editing the title
        must not silently break every link to it."""
        post = Post.objects.create(title='Original', content='x', author=self.author)
        post.title = 'Changed completely'
        post.save()
        self.assertEqual(post.slug, 'original')


class PublishingTests(BlogTestCase):
    def test_publishing_stamps_the_date(self):
        self.assertIsNotNone(self.post.published_at)

    def test_a_draft_has_no_publication_date(self):
        self.assertIsNone(self.draft.published_at)

    def test_the_date_does_not_move_when_you_fix_a_typo(self):
        original = self.post.published_at
        self.post.title = 'A published piece, corrected'
        self.post.save()
        self.post.refresh_from_db()
        self.assertEqual(self.post.published_at, original)

    def test_unpublishing_clears_the_date(self):
        post = Post.objects.create(
            title='Briefly live', content='x', author=self.author,
            status=Post.Status.PUBLISHED,
        )
        post.status = Post.Status.DRAFT
        post.save()
        self.assertIsNone(post.published_at)

    def test_published_manager_excludes_drafts(self):
        self.assertIn(self.post, Post.published.all())
        self.assertNotIn(self.draft, Post.published.all())

    def test_a_future_dated_post_is_not_published_yet(self):
        post = Post.objects.create(
            title='Tomorrow', content='x', author=self.author,
            status=Post.Status.PUBLISHED,
        )
        Post.objects.filter(pk=post.pk).update(
            published_at=timezone.now() + timezone.timedelta(days=1)
        )
        self.assertNotIn(post, Post.published.all())


class DraftVisibilityTests(BlogTestCase):
    """A draft returns 404, never 403.

    403 would confirm the URL is real, which tells a stranger the title of
    something you have not published.
    """

    def url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.draft.slug})

    def test_anonymous_visitor_gets_404(self):
        self.assertEqual(self.client.get(self.url()).status_code, 404)

    def test_a_different_author_gets_404(self):
        self.client.force_login(self.other_author)
        self.assertEqual(self.client.get(self.url()).status_code, 404)

    def test_the_author_can_read_their_own_draft(self):
        self.client.force_login(self.author)
        self.assertEqual(self.client.get(self.url()).status_code, 200)

    def test_an_editor_can_read_anyones_draft(self):
        self.client.force_login(self.editor)
        self.assertEqual(self.client.get(self.url()).status_code, 200)

    def test_drafts_stay_off_the_front_page(self):
        response = self.client.get(reverse('blog:home'))
        self.assertNotContains(response, 'A quiet draft')

    def test_drafts_stay_out_of_search_results(self):
        response = self.client.get(reverse('blog:post_list'), {'q': 'quiet'})
        self.assertNotContains(response, 'A quiet draft')


class CommentTests(BlogTestCase):
    def url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.post.slug})

    def test_anonymous_visitor_sees_no_comment_form(self):
        response = self.client.get(self.url())
        self.assertContains(response, 'to join in')
        self.assertNotContains(response, 'Post comment')

    def test_anonymous_post_is_bounced_to_the_login_page(self):
        response = self.client.post(self.url(), {'content': 'Sneaking one in'})
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)
        self.assertEqual(Comment.objects.count(), 0)

    def test_a_logged_in_reader_can_comment(self):
        self.client.force_login(self.reader)
        response = self.client.post(self.url(), {'content': 'Genuinely useful, thanks.'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comment.objects.count(), 1)

    def test_the_comment_is_signed_by_the_logged_in_user(self):
        """The form has no author field, so this cannot be forged by posting
        one — which is exactly why it has no author field."""
        self.client.force_login(self.reader)
        self.client.post(self.url(), {'content': 'Signed, sealed.', 'author': self.editor.pk})
        self.assertEqual(Comment.objects.get().author, self.reader)

    def test_you_cannot_comment_on_someone_elses_draft(self):
        self.client.force_login(self.reader)
        url = reverse('blog:post_detail', kwargs={'slug': self.draft.slug})
        self.assertEqual(self.client.post(url, {'content': 'Hello?'}).status_code, 404)


class CommentModerationTests(BlogTestCase):
    def setUp(self):
        self.comment = Comment.objects.create(
            post=self.post, author=self.reader, content='A comment worth moderating.'
        )

    def test_an_author_can_delete_their_own_comment(self):
        self.client.force_login(self.reader)
        url = reverse('blog:comment_delete', kwargs={'pk': self.comment.pk})
        self.client.post(url)
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_a_stranger_cannot_delete_someone_elses_comment(self):
        self.client.force_login(self.other_author)
        url = reverse('blog:comment_delete', kwargs={'pk': self.comment.pk})
        self.assertEqual(self.client.post(url).status_code, 403)
        self.assertTrue(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_a_moderator_can_delete_anyones_comment(self):
        self.client.force_login(self.editor)
        url = reverse('blog:comment_delete', kwargs={'pk': self.comment.pk})
        self.client.post(url)
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_hiding_a_comment_needs_the_custom_permission(self):
        self.client.force_login(self.reader)
        url = reverse('blog:comment_toggle', kwargs={'pk': self.comment.pk})
        self.assertEqual(self.client.post(url).status_code, 403)

    def test_a_moderator_can_hide_a_comment(self):
        self.client.force_login(self.editor)
        url = reverse('blog:comment_toggle', kwargs={'pk': self.comment.pk})
        self.client.post(url)
        self.comment.refresh_from_db()
        self.assertFalse(self.comment.is_approved)

    def test_a_hidden_comment_is_invisible_to_other_readers(self):
        self.comment.is_approved = False
        self.comment.save()
        self.client.force_login(self.other_author)
        response = self.client.get(self.post.get_absolute_url())
        self.assertNotContains(response, 'A comment worth moderating.')

    def test_a_hidden_comment_is_still_visible_to_its_author(self):
        self.comment.is_approved = False
        self.comment.save()
        self.client.force_login(self.reader)
        response = self.client.get(self.post.get_absolute_url())
        self.assertContains(response, 'A comment worth moderating.')

    def test_deleting_a_comment_requires_post_not_get(self):
        """A GET must never change anything — a link prefetcher would fire it."""
        self.client.force_login(self.reader)
        url = reverse('blog:comment_delete', kwargs={'pk': self.comment.pk})
        self.assertEqual(self.client.get(url).status_code, 405)


class WritingPermissionTests(BlogTestCase):
    def test_anonymous_visitor_is_sent_to_the_login_page(self):
        response = self.client.get(reverse('blog:post_create'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_a_reader_cannot_reach_the_write_page(self):
        self.client.force_login(self.reader)
        self.assertEqual(self.client.get(reverse('blog:post_create')).status_code, 403)

    def test_an_author_can_reach_the_write_page(self):
        self.client.force_login(self.author)
        self.assertEqual(self.client.get(reverse('blog:post_create')).status_code, 200)

    def test_a_new_post_belongs_to_whoever_wrote_it(self):
        self.client.force_login(self.author)
        self.client.post(reverse('blog:post_create'), {
            'title': 'Filed from the desk',
            'content': 'word ' * 40,
            'category': self.section.pk,
            'status': Post.Status.DRAFT,
        })
        self.assertEqual(Post.objects.get(title='Filed from the desk').author, self.author)

    def test_an_author_cannot_edit_someone_elses_post(self):
        self.client.force_login(self.other_author)
        url = reverse('blog:post_edit', kwargs={'slug': self.post.slug})
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_an_author_can_edit_their_own_post(self):
        self.client.force_login(self.author)
        url = reverse('blog:post_edit', kwargs={'slug': self.post.slug})
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_an_editor_can_edit_anyones_post(self):
        self.client.force_login(self.editor)
        url = reverse('blog:post_edit', kwargs={'slug': self.post.slug})
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_an_author_can_publish_their_own_draft(self):
        self.client.force_login(self.author)
        self.client.post(reverse('blog:post_publish', kwargs={'slug': self.draft.slug}))
        self.draft.refresh_from_db()
        self.assertTrue(self.draft.is_published)

    def test_deleting_shows_a_confirmation_page_before_it_deletes(self):
        self.client.force_login(self.author)
        url = reverse('blog:post_delete', kwargs={'slug': self.post.slug})
        self.assertContains(self.client.get(url), 'Yes, delete it')
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())


class DashboardTests(BlogTestCase):
    def test_the_desk_needs_a_login(self):
        response = self.client.get(reverse('blog:dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_an_author_sees_their_own_drafts(self):
        self.client.force_login(self.author)
        self.assertContains(self.client.get(reverse('blog:dashboard')), 'A quiet draft')

    def test_an_author_does_not_see_the_review_queue(self):
        self.client.force_login(self.author)
        self.assertNotContains(
            self.client.get(reverse('blog:dashboard')), 'Drafts by other people'
        )

    def test_an_editor_sees_everyone_elses_drafts(self):
        self.client.force_login(self.editor)
        response = self.client.get(reverse('blog:dashboard'))
        self.assertContains(response, 'Drafts by other people')
        self.assertContains(response, 'A quiet draft')


class FormTests(BlogTestCase):
    def test_a_one_word_title_is_rejected(self):
        form = PostForm(data={'title': 'Hi', 'content': 'word ' * 40, 'status': 'draft'})
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_a_stub_article_is_rejected(self):
        form = PostForm(data={'title': 'A real title', 'content': 'Too short.', 'status': 'draft'})
        self.assertFalse(form.is_valid())
        self.assertIn('content', form.errors)

    def test_the_comment_form_has_no_identity_field(self):
        self.assertEqual(list(CommentForm().fields), ['content'])

    def test_a_two_character_comment_is_rejected(self):
        self.assertFalse(CommentForm(data={'content': 'ok'}).is_valid())


class QueryCountTests(BlogTestCase):
    """The N+1 tripwire.

    `with_related()` collapses the per-row category and author lookups into
    the list query. If someone removes it, this fails and says why.
    """

    def test_the_front_page_does_not_query_per_post(self):
        for i in range(6):
            Post.objects.create(
                title=f'Filler {i}', content='word ' * 30,
                author=self.author, category=self.section,
                status=Post.Status.PUBLISHED,
            )
        with self.assertNumQueries(3):
            self.client.get(reverse('blog:home'))


class TemplateTagTests(BlogTestCase):
    def render(self, template, **context):
        return Template('{% load blog_extras %}' + template).render(Context(context))

    def test_query_string_keeps_the_search_term(self):
        response = self.client.get(reverse('blog:post_list'), {'q': 'django'})
        out = self.render(
            '{% query_string page=2 %}', request=response.wsgi_request
        )
        self.assertIn('q=django', out)
        self.assertIn('page=2', out)

    def test_initials_of_a_full_name(self):
        self.assertEqual(self.render('{{ u|initials }}', u=self.editor), 'ED')

    def test_display_name_prefers_the_real_name(self):
        self.editor.first_name, self.editor.last_name = 'Meghana', 'Rao'
        self.assertEqual(self.render('{{ u|display_name }}', u=self.editor), 'Meghana Rao')


class SignalTests(TestCase):
    def test_a_new_account_lands_in_the_default_group(self):
        call_command('sync_roles', verbosity=0)
        user = User.objects.create_user(username='fresh', password='testpass123')
        self.assertTrue(user.groups.filter(name='Authors').exists())
        self.assertTrue(user.has_perm('blog.add_post'))

    def test_a_superuser_is_not_put_in_a_group(self):
        call_command('sync_roles', verbosity=0)
        boss = User.objects.create_superuser(username='boss', password='testpass123')
        self.assertFalse(boss.groups.exists())

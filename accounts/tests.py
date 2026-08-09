"""Tests for registration and the login/logout cycle.

Django's own auth views are already tested by Django. What is ours is the
registration form (we added a required email), the auto-login after signup,
and the fact that a brand new account can immediately do something useful.
"""

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class RegistrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('sync_roles', verbosity=0)

    def payload(self, **overrides):
        data = {
            'username': 'newcomer',
            'email': 'newcomer@example.com',
            'password1': 'a-decent-passphrase-42',
            'password2': 'a-decent-passphrase-42',
        }
        data.update(overrides)
        return data

    def test_the_signup_page_renders(self):
        self.assertEqual(self.client.get(reverse('register')).status_code, 200)

    def test_signing_up_creates_an_account(self):
        self.client.post(reverse('register'), self.payload())
        self.assertTrue(User.objects.filter(username='newcomer').exists())

    def test_signing_up_logs_you_straight_in(self):
        response = self.client.post(reverse('register'), self.payload(), follow=True)
        self.assertTrue(response.context['user'].is_authenticated)

    def test_email_is_required(self):
        response = self.client.post(reverse('register'), self.payload(email=''))
        self.assertEqual(response.status_code, 200)   # re-rendered with errors
        self.assertFalse(User.objects.filter(username='newcomer').exists())

    def test_mismatched_passwords_are_rejected(self):
        response = self.client.post(
            reverse('register'), self.payload(password2='something-else-entirely')
        )
        self.assertFormError(
            response.context['form'], 'password2',
            'The two password fields didn’t match.',
        )

    def test_a_password_that_is_all_digits_is_rejected(self):
        """AUTH_PASSWORD_VALIDATORS in settings.py, doing its job."""
        response = self.client.post(
            reverse('register'), self.payload(password1='84726194', password2='84726194')
        )
        self.assertFalse(User.objects.filter(username='newcomer').exists())
        self.assertTrue(response.context['form'].errors)

    def test_a_new_account_can_write_immediately(self):
        self.client.post(reverse('register'), self.payload())
        self.assertEqual(self.client.get(reverse('blog:post_create')).status_code, 200)


class LoginLogoutTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('sync_roles', verbosity=0)
        cls.user = User.objects.create_user(username='regular', password='testpass123')

    def test_login_page_renders(self):
        self.assertEqual(self.client.get(reverse('login')).status_code, 200)

    def test_logging_in_works(self):
        response = self.client.post(
            reverse('login'), {'username': 'regular', 'password': 'testpass123'}, follow=True
        )
        self.assertTrue(response.context['user'].is_authenticated)

    def test_a_wrong_password_does_not_say_which_half_was_wrong(self):
        response = self.client.post(
            reverse('login'), {'username': 'regular', 'password': 'nope'}
        )
        self.assertFalse(response.context['user'].is_authenticated)
        self.assertContains(response, 'Please enter a correct username and password')

    def test_next_sends_you_back_where_you_came_from(self):
        target = reverse('blog:dashboard')
        response = self.client.post(
            f'{reverse("login")}?next={target}',
            {'username': 'regular', 'password': 'testpass123', 'next': target},
        )
        self.assertRedirects(response, target)

    def test_logging_out_needs_a_post(self):
        """Django 5 dropped GET logout on purpose: a stray <img src> or a link
        prefetcher could otherwise sign people out."""
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)

    def test_logging_out_works(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('logout'), follow=True)
        self.assertFalse(response.context['user'].is_authenticated)

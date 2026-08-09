from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blog'
    verbose_name = 'Blog'

    def ready(self):
        """Called once, after the app registry is populated.

        Importing `signals` is the whole reason this method exists — the
        `@receiver` decorators only connect when the module is imported, and
        nothing else imports it. Keep `ready()` cheap and never query the
        database from it; migrations run before the tables exist.
        """
        from . import signals  # noqa: F401

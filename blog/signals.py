"""Signals: code that runs because something happened, not because something
called it.

Two receivers live here.

Use them for genuine side effects that are nobody's business but the app's —
housekeeping, cache busting, a default group. Do *not* use them for business
logic you will later need to find: a signal is an invisible function call, and
six months from now nobody will know why saving a user touched the group table.
When the logic belongs to a view, put it in the view.
"""

from django.conf import settings
from django.contrib.auth.models import Group
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Post
from .roles import DEFAULT_ROLE


@receiver(post_save, sender=settings.AUTH_USER_MODEL, dispatch_uid='blog.default_role')
def give_new_user_the_default_role(sender, instance, created, **kwargs):
    """Every new account joins `Authors` so it can comment and write.

    `dispatch_uid` stops the receiver being connected twice if this module is
    ever imported twice — a classic cause of "why did that run three times".
    """
    if not created or instance.is_superuser:
        return
    group = Group.objects.filter(name=DEFAULT_ROLE).first()
    if group is not None:
        instance.groups.add(group)


@receiver(post_delete, sender=Post, dispatch_uid='blog.cleanup_cover')
def delete_cover_file(sender, instance, **kwargs):
    """Deleting a row does not delete the file it points at.

    Django stopped doing that in 1.3 on purpose: a rolled-back transaction
    cannot un-delete a file. So we clean up here, and never touch the shared
    default cover.
    """
    image = instance.featured_image
    if image and image.name != Post._meta.get_field('featured_image').get_default():
        image.delete(save=False)

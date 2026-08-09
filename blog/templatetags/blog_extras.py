"""Custom template tags and filters.

Django templates deliberately cannot call functions with arguments. When a
template needs a computation that a model property cannot express — anything
that depends on the *request*, or takes parameters — this is where it goes.

For this module to be loadable three things must be true:
  1. it lives in an app in INSTALLED_APPS, inside a `templatetags/` package
  2. that package has an `__init__.py`
  3. the template says `{% load blog_extras %}`

The module name is the load name. Restart the dev server after creating one:
the template tag registry is built at startup and does not autoreload.
"""

from django import template

from ..models import Post

register = template.Library()


@register.simple_tag(takes_context=True)
def query_string(context, **kwargs):
    """Rebuild the current querystring with a few keys changed.

        {% query_string page=3 %}   ->  ?q=django&category=web&page=3
        {% query_string page=None %} -> ?q=django&category=web

    Pagination links that lose the search box are the classic bug this fixes.
    """
    request = context.get('request')
    params = request.GET.copy() if request else {}
    for key, value in kwargs.items():
        if value in (None, ''):
            params.pop(key, None)
        else:
            params[key] = value
    encoded = params.urlencode()
    return f'?{encoded}' if encoded else ''


@register.filter
def display_name(user):
    """'Aviral Ale' if we know it, otherwise the username."""
    if not user or not getattr(user, 'is_authenticated', False):
        return 'Anonymous'
    return user.get_full_name() or user.get_username()


@register.filter
def initials(user):
    """One or two letters for the little printed square next to a comment."""
    name = display_name(user)
    parts = [p for p in name.replace('.', ' ').replace('_', ' ').split() if p]
    if not parts:
        return '?'
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


@register.inclusion_tag('blog/partials/_recent.html')
def recent_posts(count=3, exclude=None):
    """Renders a partial instead of returning a string.

    The dict this returns becomes the context of `_recent.html`.
    """
    posts = Post.published.with_related()
    if exclude is not None:
        posts = posts.exclude(pk=exclude.pk)
    return {'posts': posts[:count]}

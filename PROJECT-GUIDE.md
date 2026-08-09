# Blog CMS — The Complete Project Guide

A Django project explained from the first command to the last test. Every feature in this
codebase, in the order it was built, with the code that makes it work and the reasoning
behind it.

---

## How to read this

This is not a reference manual you dip into. It is the story of one project, told in the
order the pieces arrived, because that is the order in which the *reasons* make sense. The
custom permission chapter is unreadable before the model chapter, and the model chapter is
pointless before you know what a request is.

The document is in seventeen parts.

**Parts 1 to 4** are the basics: what Django is, how a request becomes a page, models,
migrations, the admin and forms. If you have built one Django tutorial app you can skim
these, but read the migration chapter — it is where most people's understanding is thinnest.

**Parts 5 to 8** are the middle: authentication, authorisation, drafts and signed comments.
This is the substance of the project. Custom permissions, groups, ownership rules, custom
managers, and the three-step migration that changes a table with live data in it.

**Parts 9 to 15** are the depth: every view annotated, custom template tags, management
commands, testing, performance, security and what changes when you deploy.

**Parts 16 and 17** are reference tables and exercises.

Code blocks are the real code from this project, not simplified sketches. Where a file is
shown in full it says so.

> Everything here has been run. The test suite is 64 tests and passes; the seed command
> builds the site the screenshots would show if this were a book with screenshots.

---

## What we are building

A small magazine called *Ctrl Bits*. Server-rendered HTML, SQLite, Pillow for images, and
nothing else — no JavaScript framework, no build step, no CSS framework.

The finished feature list:

- Articles with a title, body, cover image, section and author
- URL slugs generated from the title, with collision handling
- Sections (categories) with their own pages
- Comments that require an account, signed by the logged-in user
- **Draft and published status**, where a draft is visible only to its author and the editors
- Registration, login, logout
- **Three roles** — Readers, Authors, Editors — built from Django groups and permissions
- **Two custom permissions**: publish anyone's post, moderate anyone's comment
- Ownership rules: an author edits their own work and nobody else's
- A dashboard showing your own posts, drafts included, and for editors a review queue
- Comment moderation: hide, restore, delete
- Search, section filtering and pagination that survive each other
- Flash messages, custom 403 and 404 pages
- A seeding command that builds the whole demo site from plain data
- 64 tests

---

# Part 1 — Foundations

## 1.1 What Django actually is

Django is a program that turns an HTTP request into an HTTP response. Everything else is
detail.

A browser sends a request — a method (`GET`, `POST`), a path (`/post/hello/`), some headers,
maybe a body. Django hands that request to a chain of *middleware*, then to a *view*, and the
view returns a *response*: a status code, some headers and usually a blob of HTML. The
browser draws it.

The pattern is usually called **MVT**: Model, View, Template.

| Piece | File | Job |
| --- | --- | --- |
| **Model** | `models.py` | What the data looks like, and the rules that belong to it |
| **View** | `views.py` | What happens when a URL is requested |
| **Template** | `templates/` | What the HTML looks like |

The thing that trips people coming from other frameworks: Django's "view" is what most
frameworks call a controller, and Django's "template" is what they call a view. Do not fight
it, just learn the words.

The full path of one request through this project:

```
1.  Browser            GET /post/caching-is-a-bet-about-the-future/
2.  WSGI server        hands the raw request to Django
3.  Middleware         session loaded, request.user attached, CSRF checked
4.  core/urls.py       not /admin/, not /accounts/ → include('blog.urls')
5.  blog/urls.py       matches 'post/<slug:slug>/', slug="caching-is-..."
6.  blog/views.py      post_detail(request, slug='caching-is-...')
7.  blog/models.py     the ORM builds SQL, the database answers
8.  templates/         post_detail.html renders with that data
9.  Middleware         response headers added on the way back out
10. Browser            draws the page
```

Steps 4 through 8 are the parts you write. The rest is Django's.

## 1.2 The environment

Django 6.0 needs Python 3.12 or newer.

```bash
python3 --version
```

A **virtual environment** is a private folder of Python packages for one project. Without one,
every project on your machine shares the same packages and upgrading one breaks another.

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: .\venv\Scripts\Activate.ps1
```

Your prompt gains a `(venv)` prefix. That prefix is the only reliable way to know it worked.
You must activate it in every new terminal, forever.

```bash
pip install django pillow
pip freeze > requirements.txt
```

`requirements.txt` is how someone else reproduces your environment exactly:

```
asgiref==3.12.1
Django==6.0.7
pillow==12.3.0
sqlparse==0.5.5
```

You installed two things and got four. `asgiref` and `sqlparse` are Django's own
dependencies. Pin them all — "it works on my machine" is almost always a dependency you did
not know you had.

## 1.3 Starting the project

```bash
django-admin startproject core .
```

The trailing dot matters. Without it you get `core/core/`, which works but reads badly for
the rest of the project's life. With it:

```
manage.py
core/
├── __init__.py
├── settings.py
├── urls.py
├── wsgi.py
└── asgi.py
```

**`manage.py`** — a thin wrapper that sets `DJANGO_SETTINGS_MODULE` and calls Django's
command-line handler. You will type it thousands of times. It is not special; it exists so
that `python manage.py migrate` knows which settings to load.

**`core/settings.py`** — one Python module of module-level constants. That is all a Django
settings file is. Because it is Python, you can compute values in it, which is how
environment-specific settings get done.

**`core/urls.py`** — the root URL map. Every request starts here.

**`core/wsgi.py` and `core/asgi.py`** — the entry points a production server imports. WSGI is
the synchronous protocol, ASGI the async one. Ignore both until you deploy.

Run it:

```bash
python manage.py runserver
```

You get the rocket page and a warning about unapplied migrations. Both are expected.

## 1.4 Settings, the parts that matter

The generated file is long. These are the lines you will actually touch.

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
```

`__file__` is `core/settings.py`, so `.parent` is `core/` and `.parent.parent` is the project
root. Everything else builds paths from `BASE_DIR`, which is why the project runs from any
directory.

```python
SECRET_KEY = 'django-insecure-++q33x_p&-wyv&+p#b9o54cp2r8ydcz^a)t#xin@9@y2xb0vys'
DEBUG = True
ALLOWED_HOSTS = []
```

`SECRET_KEY` signs sessions, password-reset tokens and CSRF tokens. Anyone who has it can
forge all three. The `django-insecure-` prefix is Django telling you this one was generated
for development and must not ship.

`DEBUG = True` gives you the yellow traceback page, serves static files automatically, and
disables a pile of security behaviour. In production it is `False`, and then `ALLOWED_HOSTS`
must list your real domains or every request is rejected.

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'blog',
    'accounts',
]
```

An **app** is a Python package Django knows about. Being in this list is what makes Django
look for its models, its migrations, its template tags and its templates. Forgetting to add
an app here is the single most common "why is nothing happening" bug.

The six `django.contrib` entries are apps too, shipped with Django:

| App | What it gives you |
| --- | --- |
| `admin` | the `/admin/` backend |
| `auth` | User, Group, Permission, login machinery |
| `contenttypes` | a registry of every model, which permissions are keyed on |
| `sessions` | server-side session storage, how login persists |
| `messages` | one-shot flash messages between requests |
| `staticfiles` | finding and serving CSS/JS/images |

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

Middleware wraps every request, in order on the way in and reverse order on the way out.
`SessionMiddleware` reads the session cookie; `AuthenticationMiddleware` uses it to attach
`request.user`. That ordering is a hard dependency — auth cannot run before sessions, which
is why the list order is not cosmetic.

```python
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]
```

`DIRS` is the project-wide template folder, searched first. `APP_DIRS` also searches
`<app>/templates/` in every installed app. This project uses a single top-level `templates/`
folder because it is easier to see the whole design at once.

**Context processors** are functions that add variables to every template's context. That
is where `user`, `perms`, `messages` and `request` come from in a template — you never pass
them, they are always there.

```python
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'blog:home'
LOGOUT_REDIRECT_URL = 'blog:home'
```

**Static** files are yours and ship with the code: CSS, JS, logos. **Media** files are
uploaded by users at runtime. Different lifecycles, different folders, different servers in
production. Never mix them.

The three `LOGIN_*` settings are what `@login_required` and the auth views use, and they
accept URL *names*, not paths.

## 1.5 Creating the app

```bash
python manage.py startapp blog
```

```
blog/
├── __init__.py
├── admin.py          ← register models with /admin/
├── apps.py           ← app configuration and startup hooks
├── models.py         ← the tables
├── tests.py          ← the tests
├── views.py          ← the request handlers
└── migrations/       ← the database's version history
```

Two things `startapp` does not create and you will need: **`urls.py`**, because Django cannot
know how you want to route, and **`templates/`**, because this project keeps them at the top
level.

Add it to `INSTALLED_APPS` immediately. Nothing works until you do.

## 1.6 The first view and URL

A view is a function that takes a request and returns a response.

```python
# blog/views.py
from django.http import HttpResponse

def index(request):
    return HttpResponse("<h1>Hello</h1>")
```

That is a complete, working Django view. Everything else — templates, the ORM, forms — is a
convenience for producing that response.

```python
# blog/urls.py
from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.index, name='home'),
]
```

```python
# core/urls.py
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('blog.urls')),
]
```

Three details in `path()` that matter for the rest of the project:

**The route has no leading slash.** `include()` has already consumed the prefix, so patterns
are relative to it.

**`name=` is the point.** Never hardcode a URL. Write `{% url 'blog:home' %}` in a template
or `reverse('blog:home')` in Python. Then when the path changes, one line changes and every
link follows.

**`app_name` creates the namespace.** With it, every name becomes `blog:<name>`. That is why
this project's URLs are `blog:post_detail` and not `post_detail`, and it is what lets a second
app have its own `home` without a collision.

### Order matters

```python
urlpatterns = [
    path('post/new/', views.post_create, name='post_create'),
    path('post/<slug:slug>/', views.post_detail, name='post_detail'),
]
```

Django takes the **first** pattern that matches. If those two swap places, `/post/new/`
matches `<slug:slug>` with `slug="new"`, and the create page 404s while you stare at code
that looks correct.

### Path converters

| Converter | Matches | Example |
| --- | --- | --- |
| `str` | any text without `/` (the default) | `<str:name>` |
| `int` | digits, passed as an `int` | `<int:pk>` |
| `slug` | letters, digits, hyphens, underscores | `<slug:slug>` |
| `uuid` | a UUID | `<uuid:token>` |
| `path` | anything, including `/` | `<path:subpath>` |

This project uses `<slug:slug>` for posts and sections and `<int:pk>` for comments. Using
`slug` instead of `str` is a small piece of free validation: a URL with a `.` or a space in
the slug position never reaches your view at all.

## 1.7 Templates

Returning HTML from Python strings stops being funny immediately. Templates are HTML files
with holes in them.

```python
from django.shortcuts import render

def index(request):
    posts = Post.objects.all()
    return render(request, 'blog/home.html', {'posts': posts})
```

`render()` does three things: finds the template, renders it with that dictionary (the
**context**), and wraps the result in an `HttpResponse`.

```html
{% for post in posts %}
    <h2>{{ post.title }}</h2>
    <p>{{ post.excerpt }}</p>
{% empty %}
    <p>Nothing published yet.</p>
{% endfor %}
```

`{{ }}` prints a value. `{% %}` runs a tag. `{% empty %}` is a small kindness — the block that
runs when the loop had nothing to iterate.

**Dot lookup** in a template tries four things in order: dictionary key, attribute,
method-with-no-arguments, list index. That is why `{{ post.title }}`, `{{ post.excerpt }}`
(a property), `{{ post.get_absolute_url }}` (a method) and `{{ post.comments.count }}` all
work with identical syntax. It is also why templates cannot pass arguments to a method —
that restriction is deliberate, and it is what custom template tags exist to work around.

### Autoescaping

```html
{{ post.content }}
```

If `content` contains `<script>alert(1)</script>`, the browser shows that text; it does not
run it. Django escapes every variable by default. This is the reason cross-site scripting is
rare in Django apps and common everywhere else.

The escape hatches are `|safe` and `{% autoescape off %}`, and both mean "I have personally
verified this HTML is trustworthy". This project never uses them on user input.

### Filters used in this project

| Filter | Does | Used in |
| --- | --- | --- |
| `linebreaks` | blank lines to `<p>`, single to `<br>` | article and comment bodies |
| `date:"j F Y"` | formats a datetime | bylines |
| `default:x` | falls back when the value is empty | the byline date, falling back to `created_at` |
| `pluralize` | adds "s" when the count is not 1 | "3 pieces", "1 piece" |
| `urlencode` | escapes for a querystring | search links |
| `length` | count | comment headings |

## 1.8 Template inheritance

Every page shares a masthead, a nav and a footer. Copying that into eight files means
changing it in eight files.

```html
{# templates/base.html — abridged #}
<!DOCTYPE html>
<html lang="en">
<head>
    <title>{% block title %}{% endblock %} · Ctrl Bits</title>
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
</head>
<body>
    <header class="masthead"> ... nav ... </header>

    {% if messages %}
        <div class="shell messages" role="status">
            {% for message in messages %}
                <p class="message message--{{ message.tags|default:'info' }}">{{ message }}</p>
            {% endfor %}
        </div>
    {% endif %}

    <main>{% block content %}{% endblock %}</main>

    <footer class="footer"> ... </footer>
</body>
</html>
```

```html
{# templates/blog/home.html #}
{% extends 'base.html' %}
{% load blog_extras %}

{% block title %}Latest{% endblock %}

{% block content %}
    <div class="shell"> ... the page ... </div>
{% endblock %}
```

Rules worth memorising:

`{% extends %}` must be the **first tag** in the file. Nothing before it, not even a comment.

Anything outside a `{% block %}` in a child template is **discarded silently**. Content that
mysteriously does not appear is nearly always sitting outside a block.

`{% block %}` names must be unique in a template.

`{{ block.super }}` inside a block includes the parent's version rather than replacing it.

### Three ways to reuse markup

| Mechanism | Use when |
| --- | --- |
| `{% extends %}` | the child *is* a page and the parent is its frame |
| `{% include %}` | a fragment repeats, and it can read the surrounding context |
| inclusion tag | a fragment needs data the surrounding view did not fetch |

This project uses all three. `{% include 'blog/partials/_card.html' %}` renders one post card
and reads `post` straight from the enclosing loop. `{% recent_posts 3 %}` is an inclusion tag,
because the footer wants three recent posts and no view puts them in the context.

## 1.9 Static files

```python
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
```

```html
{% load static %}
<link rel="stylesheet" href="{% static 'css/style.css' %}">
```

Never hardcode `/static/css/style.css`. The `{% static %}` tag routes through the configured
storage backend, which in production may add a content hash to the filename for cache-busting.
Hardcode the path and you get a stale stylesheet on every deploy, for every user, forever.

`{% load static %}` must appear in **every** template that uses the tag. It is not inherited
from `base.html`. Loads are per-file.

---

# Part 2 — Models and the database

## 2.1 A model is a table

```python
from django.db import models

class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
```

One class, one table. One attribute, one column. One instance, one row.

Django adds an auto-incrementing `id` primary key unless you declare your own.

### The fields this project uses

| Field | Column | Notes |
| --- | --- | --- |
| `CharField(max_length=n)` | VARCHAR | `max_length` is required and enforced by the database |
| `TextField()` | TEXT | unbounded; do **not** give it a `max_length` (see below) |
| `SlugField(max_length=n)` | VARCHAR | a CharField that validates as a slug |
| `BooleanField(default=)` | BOOLEAN | `is_approved` |
| `DateTimeField(auto_now_add=True)` | TIMESTAMP | set once, on insert |
| `DateTimeField(auto_now=True)` | TIMESTAMP | overwritten on every save |
| `DateTimeField(null=True)` | TIMESTAMP | nullable, set by hand — `published_at` |
| `ImageField(upload_to=)` | VARCHAR | stores a path; needs Pillow |
| `ForeignKey(...)` | INTEGER + FK | a link to one row in another table |

### A real bug this project had

```python
content = models.TextField(max_length=100)     # wrong
```

`TextField` ignores `max_length` at the database level — but `ModelForm` does not. It builds
a validator from it. The result was a form that silently refused any article longer than a
tweet, with an error message that pointed at the user rather than the model. It looked like a
form bug for weeks. It was a model typo.

```python
content = models.TextField()                   # right
```

If you want a genuine cap, use `CharField`, or add an explicit validator, and say so.

## 2.2 Migrations

A migration is a Python file describing a change to the database schema. Together they are
version control for your tables.

```bash
python manage.py makemigrations      # model changes  → a migration file
python manage.py migrate             # migration file → the database
```

Two commands, always in that order, always both. Editing a model and running only `migrate`
does nothing at all, which is the second most common "why is nothing happening" bug.

A generated migration is readable:

```python
class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.BigAutoField(primary_key=True, ...)),
                ('title', models.CharField(max_length=200)),
                ('content', models.TextField()),
            ],
        ),
    ]
```

`dependencies` is what makes them a graph rather than a list, so migrations from different
apps can interleave correctly.

Useful commands:

```bash
python manage.py showmigrations             # what is applied
python manage.py sqlmigrate blog 0009       # the SQL a migration will run
python manage.py migrate blog 0008          # roll back to 0008
python manage.py makemigrations --check     # CI: fail if models drifted
```

`sqlmigrate` is the one people never learn and should. Before any migration touches a
database with real data in it, read the SQL. It takes twenty seconds and it is the difference
between a deploy and an incident.

> Migration files are **code**. Commit them. Review them. Never edit an applied migration —
> write a new one. The only migration you may safely delete is one nobody has run.

## 2.3 Talking to the ORM

```bash
python manage.py shell
```

```python
>>> from blog.models import Post
>>> Post.objects.create(title='Hello', content='...', author=me)
>>> Post.objects.all()
>>> Post.objects.count()
>>> Post.objects.filter(status='published')
>>> Post.objects.filter(title__icontains='django')
>>> Post.objects.exclude(category=None)
>>> Post.objects.order_by('-created_at')[:5]
>>> Post.objects.get(slug='hello')          # raises if 0 or 2+ match
>>> Post.objects.first()
```

### Field lookups

The double underscore is how you say "on this field, this comparison" — and, later, "through
this relationship".

| Lookup | SQL |
| --- | --- |
| `title__exact='x'` | `= 'x'` |
| `title__iexact='x'` | case-insensitive `=` |
| `title__contains='x'` | `LIKE '%x%'` |
| `title__icontains='x'` | case-insensitive LIKE |
| `published_at__lte=now` | `<=` |
| `category__isnull=True` | `IS NULL` |
| `status__in=['a', 'b']` | `IN (...)` |
| `category__name='Django'` | a JOIN, then `=` |

That last row is the important one. `category__name` follows the foreign key. You never write
SQL joins by hand.

### Querysets are lazy

```python
posts = Post.objects.filter(status='published')     # no query yet
posts = posts.exclude(category=None)                # still no query
for post in posts:                                  # NOW it runs
    ...
```

A queryset builds SQL until something forces evaluation: iteration, `len()`, `list()`,
slicing with a step, `bool()`, or printing it in a shell. This is why you can pass querysets
around and add filters in three different places without paying for three queries.

The corollary is the trap: a queryset re-evaluates every time you use it in a new expression
unless it has been cached by iteration. Calling `.all()` inside a template loop throws away
the cache and re-queries on every pass.

## 2.4 `__str__` and `Meta`

```python
class Category(models.Model):
    name = models.CharField(max_length=54, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name
```

Without `__str__` the admin shows `Category object (3)`. With it, it shows the name. Write one
for every model; it costs two lines and it improves the admin, the shell and every error
message you will ever read.

`Meta.ordering` gives a default `ORDER BY` so you do not repeat `order_by()` everywhere.
`verbose_name_plural` stops Django from writing "Categorys".

This project's `Post.Meta` does more:

```python
class Meta:
    ordering = ['-published_at', '-created_at']
    indexes = [
        models.Index(fields=['-published_at'], name='post_published_at_idx'),
        models.Index(fields=['status', '-published_at'], name='post_status_pub_idx'),
    ]
    permissions = [
        ('can_publish_post', 'Can publish or unpublish any post'),
    ]
```

`ordering` sorts by publication date and falls back to creation date, so drafts (which have
no `published_at`) still have a stable order. `indexes` is covered in Part 13, `permissions`
in Part 6.

> Naming indexes explicitly is a small habit worth having. Let Django generate the name and
> you get `blog_post_publish_1a2b3c_idx`, which is fine until you hand-write a migration and
> have to reproduce that hash exactly.

## 2.5 Slugs and `get_absolute_url`

`/post/42/` tells a reader nothing. `/post/caching-is-a-bet-about-the-future/` tells them
everything. That is a **slug**.

```python
def unique_slug(model, value, instance=None, field='slug'):
    """Turn `value` into a slug nothing else in `model` is using yet."""
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
```

`slugify()` lowercases, strips punctuation and turns spaces into hyphens: `My Country Nepal`
becomes `my-country-nepal`. The loop handles the collision: a second post with the same title
gets `-1`, a third gets `-2`.

Two details that are easy to get wrong.

**Excluding yourself.** Without the `instance.pk` exclusion, re-saving an existing post finds
its own slug already taken and renames it to `-1` every single time you press save.

**Only generate when empty.**

```python
def save(self, *args, **kwargs):
    if not self.slug:
        self.slug = unique_slug(Post, self.title, instance=self)
    ...
```

Once a post is published its URL is a promise. People bookmark it, other sites link to it,
search engines index it. Regenerating the slug when someone fixes a typo in the headline
breaks every one of those links. There is a test for this:

```python
def test_resaving_a_post_keeps_its_slug(self):
    post = Post.objects.create(title='Original', content='x', author=self.author)
    post.title = 'Changed completely'
    post.save()
    self.assertEqual(post.slug, 'original')
```

And the other half of the deal:

```python
def get_absolute_url(self):
    return reverse('blog:post_detail', kwargs={'slug': self.slug})
```

Now every template writes `{{ post.get_absolute_url }}`, the admin grows a "view on site"
button for free, and `redirect(post)` works because `redirect()` calls this method when you
hand it a model instance.

## 2.6 The first relationship: Category

A post belongs to one section; a section holds many posts. That is a **ForeignKey**, and it
lives on the "many" side.

```python
category = models.ForeignKey(
    Category,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='posts',
)
```

**`on_delete`** is required, and it is a real decision: what happens to this post when its
category is deleted?

| Option | Effect | Right for |
| --- | --- | --- |
| `CASCADE` | delete the post too | comments on a post, posts of a deleted user |
| `SET_NULL` | keep the post, clear the field | a category — losing a section must not lose articles |
| `PROTECT` | refuse to delete the category | anything you truly cannot afford to lose |
| `RESTRICT` | like PROTECT, but allows a cascade elsewhere in the same delete | rare |
| `SET_DEFAULT` | fall back to a default | needs a sensible default row |

`SET_NULL` requires `null=True`, because the column has to be able to hold nothing.

**`null` versus `blank`** is the distinction everyone gets wrong once:

- `null=True` — the *database* column accepts NULL
- `blank=True` — the *form* accepts an empty value

They are unrelated layers. On a text field, use `blank=True` alone and store `''`, never
`null=True`, so you do not end up with two different kinds of empty.

**`related_name`** names the reverse accessor:

```python
post.category            # forward: the Category object
category.posts.all()     # reverse: every Post in that section
```

Without `related_name` the reverse would be `category.post_set`. Naming it is worth doing:
`Count('posts')` reads better than `Count('post')`, and this project uses that in three places.

## 2.7 The second relationship: Comment

```python
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name='comments')
    content = models.TextField()
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

`CASCADE` on `post` is correct: comments on a deleted article have nothing to be about.

Note `settings.AUTH_USER_MODEL`, not `User`. Always reference the user model this way in a
`ForeignKey`. It is a string, resolved lazily, and it keeps working on the day someone swaps
in a custom user model. Importing `User` directly bakes in an assumption you may not get to
revisit.

For *code* rather than field definitions, use `get_user_model()`:

```python
from django.contrib.auth import get_user_model
User = get_user_model()
```

### Relationship summary for this project

```
Category  1 ──< Post        category.posts.all()      post.category
User      1 ──< Post        user.posts.all()          post.author
Post      1 ──< Comment     post.comments.all()       comment.post
User      1 ──< Comment     user.comments.all()       comment.author
```

Two foreign keys point at `User`, which is why they need different `related_name` values.
Both are `related_name='posts'` and `related_name='comments'` on different models, which is
fine — the names only have to be unique per target model.

## 2.8 Images: ImageField, Pillow and media

```python
featured_image = models.ImageField(
    upload_to='blog_images/',
    default='blog_images/default.png',
)
```

The column stores a **path**, not the bytes. The file goes on disk under `MEDIA_ROOT`.

`ImageField` needs Pillow installed, because it verifies that the upload is actually an image
rather than a renamed executable.

```python
# core/settings.py
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

```python
# core/urls.py — the last line of the file
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

That line only functions when `DEBUG = True`. It is a development convenience so you do not
have to run nginx to see an uploaded picture. In production, a real web server serves that
directory and Django never sees the request.

In the template:

```html
<img src="{{ post.featured_image.url }}" alt="Cover for {{ post.title }}">
```

`.url` builds `MEDIA_URL + name`. Using `{{ post.featured_image }}` instead prints the bare
path and produces a broken image, which is a five-minute bug the first time.

A form that uploads files needs two things or the file silently never arrives:

```html
<form method="post" enctype="multipart/form-data">
```

```python
form = PostForm(request.POST, request.FILES, instance=post)
```

### Deleting the file when the row goes

Django deliberately does not delete files when a row is deleted — a rolled-back transaction
cannot un-delete a file. So this project does it with a signal:

```python
@receiver(post_delete, sender=Post, dispatch_uid='blog.cleanup_cover')
def delete_cover_file(sender, instance, **kwargs):
    image = instance.featured_image
    if image and image.name != Post._meta.get_field('featured_image').get_default():
        image.delete(save=False)
```

The `get_default()` check matters: every post without a cover points at the *same* default
file, and deleting one post must not remove the house cover from all of them.

---

# Part 3 — The admin

## 3.1 Free CRUD

```python
from django.contrib import admin
from .models import Post

admin.site.register(Post)
```

Two lines and you have a working backend with list, search, add, edit, delete, and permission
checks. Nothing else in Django gives that much for that little.

```bash
python manage.py createsuperuser
```

The admin is for **staff**, not for users. It is a database editor with a nice skin. Never
build your product's user-facing features in it — the moment a non-technical user needs a
guard rail, you need a real view.

## 3.2 Making it useful

The decorator form and a `ModelAdmin` class:

```python
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'status_badge', 'category', 'author', 'comment_count', 'published_at')
    list_filter = ('status', 'category', 'author', 'created_at')
    search_fields = ('title', 'content')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    inlines = [CommentInline]
    autocomplete_fields = ('category', 'author')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at')
    actions = ['publish_selected', 'unpublish_selected']
    fieldsets = (
        (None, {'fields': ('title', 'slug', 'category', 'author')}),
        ('The piece', {'fields': ('content', 'featured_image')}),
        ('Publishing', {'fields': ('status', 'published_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
```

| Option | Effect |
| --- | --- |
| `list_display` | columns on the changelist; accepts model fields, model methods and ModelAdmin methods |
| `list_filter` | the right-hand filter sidebar |
| `search_fields` | the search box; also **required** on any model another admin autocompletes |
| `date_hierarchy` | the drill-down date bar |
| `inlines` | edit related rows on the parent's page |
| `autocomplete_fields` | replaces a 10,000-row dropdown with a search box |
| `prepopulated_fields` | JavaScript that fills the slug as you type the title |
| `readonly_fields` | shown, not editable |
| `fieldsets` | groups fields into labelled sections |

### Computed columns

```python
@admin.display(description='Status', ordering='status')
def status_badge(self, obj):
    return '● Published' if obj.is_published else '○ Draft'
```

The `@admin.display` decorator sets the column header and makes it sortable by naming the
database expression to sort on.

### Never make the admin slow

```python
def get_queryset(self, request):
    return (
        super().get_queryset(request)
        .select_related('category', 'author')
        .annotate(_comments=Count('comments'))
    )

@admin.display(description='Comments', ordering='_comments')
def comment_count(self, obj):
    return obj._comments
```

Without `select_related`, a changelist of 100 posts runs 201 queries — one for the list, one
per row for the category, one per row for the author. This is the N+1 problem (Part 13), and
the admin is where it bites first because the admin shows a hundred rows at a time.

`annotate` computes the comment count **in the database**, in the same query. Calling
`obj.comments.count()` from the method would be another 100 queries.

## 3.3 Filling in the author automatically

```python
def save_model(self, request, obj, form, change):
    if not change and not obj.author_id:
        obj.author = request.user
    super().save_model(request, obj, form, change)
```

`change` is `False` on create and `True` on edit. Note `obj.author_id` rather than
`obj.author` — reading the `_id` attribute does not trigger a database fetch, and on an
unsaved object with no author it does not raise.

## 3.4 Bulk actions with their own permission

```python
@admin.action(description='Publish selected posts', permissions=['publish'])
def publish_selected(self, request, queryset):
    updated = queryset.filter(status=Post.Status.DRAFT).update(
        status=Post.Status.PUBLISHED, published_at=timezone.now()
    )
    self.message_user(request, f'{updated} post(s) published.', messages.SUCCESS)

def has_publish_permission(self, request):
    return request.user.has_perm('blog.can_publish_post')
```

`permissions=['publish']` tells the admin to look for a method called
`has_publish_permission`. Staff without `blog.can_publish_post` do not see the action in the
dropdown at all.

Note the action uses `queryset.update()`, which issues **one** UPDATE statement and does not
call `save()` on anything. That is why `published_at` is set explicitly here — the model's
`save()` never runs. It is a genuine trade: one query instead of N, at the cost of skipping
your own model logic. Know which one you are choosing.

## 3.5 Inlines

```python
class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ('author', 'content', 'is_approved', 'created_at')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('author',)
```

`TabularInline` is a compact table; `StackedInline` is one form per row. `extra = 0` stops
Django offering three blank forms you did not ask for.

## 3.6 Admin branding

```python
admin.site.site_header = 'Blog CMS Administration'
admin.site.site_title = 'Blog CMS Admin Portal'
admin.site.index_title = 'Welcome to the Blog CMS Admin Portal'
```

Three lines, and staff can tell staging from production at a glance. Worth doing on day one.
---

# Part 4 — Forms

## 4.1 Form versus ModelForm

A `Form` is a set of fields you declare yourself. A `ModelForm` reads the fields off a model.
If the form saves a model, use a `ModelForm` — otherwise you are maintaining the same field
list in two places and they will drift.

```python
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'featured_image', 'category', 'status']
```

**Always list `fields` explicitly.** `fields = '__all__'` looks convenient and is a security
bug waiting for its moment: add a field to the model later — `is_approved`, `is_staff`,
`status` — and it silently becomes editable by anyone who can POST to that form. Listing the
fields means adding a field to a model never changes what a form accepts.

A form does four things: renders HTML, parses `request.POST`, validates, and saves. In a view:

```python
form = PostForm(request.POST, request.FILES, instance=post)
if form.is_valid():
    form.save()
```

`is_valid()` runs the whole validation chain and fills `form.errors` and `form.cleaned_data`.
Never read `request.POST['title']` directly — that value has not been validated or cleaned.

## 4.2 Widgets, labels, help text

```python
class Meta:
    model = Post
    fields = ['title', 'content', 'featured_image', 'category', 'status']
    widgets = {
        'title': forms.TextInput(attrs={'placeholder': 'Give it a headline worth clicking'}),
        'content': forms.Textarea(attrs={
            'rows': 14,
            'placeholder': 'Start writing. Blank lines make new paragraphs.',
        }),
    }
    help_texts = {
        'title': 'The URL or slug is auto-generated from the title.',
        'featured_image': 'Optional. Leave it alone and the house cover is used.',
        'status': 'Drafts are visible to you and the editors. Nobody else.',
    }
```

A **widget** is the HTML control. A **field** is the validation. Changing the widget never
changes what is accepted, which is the correct separation: making a field a `<textarea>` says
nothing about what counts as valid.

`attrs` is passed straight through to the tag, so this is also where `class`, `autocomplete`,
`inputmode` and any `data-` attribute go.

Runtime tweaks go in `__init__`, because `Meta` cannot see the instance:

```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields['category'].empty_label = 'Choose a section'
```

## 4.3 Validation

Three layers, each with a job.

**Field-level, built in.** `max_length`, `required`, `EmailField` — free, from the model.

**Field-level, yours.** A `clean_<fieldname>()` method. It runs after the field's own
validation, receives the cleaned value, and must return it.

```python
def clean_title(self):
    title = self.cleaned_data['title'].strip()
    if len(title) < 5:
        raise ValidationError('Use a real title.')
    return title

def clean_content(self):
    content = self.cleaned_data['content'].strip()
    if len(content.split()) < 20:
        raise ValidationError('Twenty words minimum. This is a magazine, not a status update.')
    return content
```

Forgetting the `return` is the classic mistake: the method returns `None`, and the field
silently becomes empty. It does not raise. You just get a blank title.

**Form-level.** A `clean()` method, for rules involving more than one field — a start date
before an end date, a password matching its confirmation. Call `super().clean()` first.

Errors raised in `clean_x` attach to field `x`; errors raised in `clean()` go to
`form.non_field_errors`, which is why every template in this project renders that block
separately:

```html
{% if form.non_field_errors %}
    <div class="notice">
        {% for error in form.non_field_errors %}{{ error }}{% endfor %}
    </div>
{% endif %}
```

## 4.4 Rendering a form by hand

`{{ form }}` works and looks like 2009. This project loops instead:

```html
{% for field in form %}
    {% include 'blog/partials/_field.html' %}
{% endfor %}
```

```html
{# templates/blog/partials/_field.html — the whole file #}
<div class="field {% if field.errors %}field--error{% endif %}">
    {{ field.label_tag }}
    {{ field }}
    {% if field.help_text %}
        <small class="field__help">{{ field.help_text }}</small>
    {% endif %}
    {% if field.errors %}
        <ul class="field__errors">
            {% for error in field.errors %}
                <li>{{ error }}</li>
            {% endfor %}
        </ul>
    {% endif %}
</div>
```

One partial, included by six templates, so every form on the site looks the same and gains an
accessibility fix in one edit. Iterating a form yields **bound fields**, which carry
`.label_tag`, `.errors`, `.help_text`, `.value` and `.id_for_label`.

A small refinement, used by both forms here:

```python
class StyledForm(forms.ModelForm):
    """Drops the ':' Django puts after every label — the CSS uses small caps."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super().__init__(*args, **kwargs)
```

## 4.5 CSRF

```html
<form method="post">
    {% csrf_token %}
    ...
</form>
```

Leave it out and every POST returns 403.

**What it prevents.** You are logged in here. You visit another site. That site contains a
hidden form that POSTs to `/post/42/delete/`. Your browser attaches your cookies, because
that is what browsers do, and the post is deleted. Nobody stole your password; they borrowed
your session.

**How the token stops it.** Django puts a random value in a cookie and the same value in a
hidden form field, and requires them to match. The attacking site can make your browser send
the cookie but cannot read it — the same-origin policy stops that — so it cannot put the
matching value in the form.

Three rules:

`{% csrf_token %}` in every POST form, no exceptions.

`GET` requests are not protected, deliberately, which is the other half of the reason a GET
must never change anything.

`@csrf_exempt` exists for APIs with a different auth scheme. If you are reaching for it on an
HTML form, something else is wrong.

## 4.6 POST, redirect, GET

```python
if form.is_valid():
    comment = form.save(commit=False)
    comment.post = post
    comment.author = request.user
    comment.save()
    messages.success(request, 'Comment posted.')
    return redirect(f'{post.get_absolute_url()}#comments')
```

Never render a page directly in response to a successful POST. Redirect. Otherwise the
browser's address bar still holds the POST, and refreshing re-submits it — that is the
"Confirm form resubmission" dialog, and the reason forums used to be full of double posts.

### `commit=False`

```python
comment = form.save(commit=False)     # build the instance, do not hit the database
comment.post = post                   # fill in what the form does not know
comment.author = request.user
comment.save()                        # now write it
```

This is the single most important pattern in the project. The form is what the *browser* sent;
`commit=False` gives you the object before it is saved so the *server* can fill in the fields
the browser must not control.

`CommentForm` has exactly one field, `content`. The author is not a form field, so no amount
of crafted POST data can set it. There is a test that proves it:

```python
def test_the_comment_is_signed_by_the_logged_in_user(self):
    self.client.force_login(self.reader)
    self.client.post(self.url(), {'content': 'Signed, sealed.', 'author': self.editor.pk})
    self.assertEqual(Comment.objects.get().author, self.reader)
```

The POST contains `author`. It is ignored. That is the whole defence, and it is structural
rather than a check somebody has to remember to write.

> If you take one rule from this document: **identity never travels through a form.** Anything
> the browser sends is a suggestion.

Note also that when you use `commit=False` on a form with a many-to-many field you must call
`form.save_m2m()` afterwards. This project has no M2M yet — it is the first thing that bites
when you add tags.

---

# Part 5 — Authentication: who are you

Authentication is identity. Authorisation, in Part 6, is permission. Conflating them is how
you end up with a logged-in user deleting somebody else's article.

## 5.1 The User model

`django.contrib.auth` ships a `User` with `username`, `password`, `email`, `first_name`,
`last_name`, `is_active`, `is_staff`, `is_superuser`, `date_joined`, `last_login`, plus
`groups` and `user_permissions`.

Three flags people mix up:

| Flag | Means |
| --- | --- |
| `is_active` | the account works. Setting it `False` is how you disable an account without deleting its posts |
| `is_staff` | may log into `/admin/`. Says nothing about what they can do there |
| `is_superuser` | **every** permission check returns True, unconditionally |

That last one matters when you are testing authorisation. A superuser can do everything, so
testing your permission rules while logged in as one proves nothing. This project's tests use
ordinary accounts for exactly that reason.

Reference it correctly:

```python
# in a model field — a lazy string, survives a custom user model
author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

# in code
from django.contrib.auth import get_user_model
User = get_user_model()
```

## 5.2 Login and logout for free

```python
# core/urls.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/register/', accounts_views.register, name='register'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('blog.urls')),
]
```

That one `include` gives you:

| URL | Name | View |
| --- | --- | --- |
| `/accounts/login/` | `login` | `LoginView` |
| `/accounts/logout/` | `logout` | `LogoutView` |
| `/accounts/password_change/` | `password_change` | `PasswordChangeView` |
| `/accounts/password_reset/` | `password_reset` | `PasswordResetView` |
| ...and the reset confirm/complete pair | | |

You write no view code. You only supply templates, and Django looks for them in
`templates/registration/`. This project supplies two: `login.html` and `register.html`.

```python
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'blog:home'
LOGOUT_REDIRECT_URL = 'blog:home'
```

All three accept URL *names*. `LOGIN_URL` is where `@login_required` sends anonymous
visitors.

### Logging out is a POST

```html
<form method="post" action="{% url 'logout' %}" class="nav__form">
    {% csrf_token %}
    <button type="submit" class="linkish">Log out</button>
</form>
```

Django 5 removed GET logout deliberately. A `<img src="/accounts/logout/">` on any page, or a
browser's link prefetcher, could otherwise sign people out. It is the same principle as the
delete confirmation: a GET must never change state. There is a test:

```python
def test_logging_out_needs_a_post(self):
    self.client.force_login(self.user)
    self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
```

## 5.3 Registration

Django does not ship a signup view, because what a signup form should collect is a product
decision. This project's is eleven lines:

```python
# accounts/forms.py — the whole file
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')
```

`UserCreationForm` already handles the two password fields, the confirmation match, the
uniqueness of the username and running the password validators. Subclassing it to add a
required email is the whole customisation.

```python
# accounts/views.py — the whole file
from django.contrib.auth import login
from django.shortcuts import render, redirect
from .forms import RegisterForm

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('blog:home')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})
```

That `if request.method == 'POST' / else` shape is the standard Django form view, and you
will write it a hundred times: POST means "they submitted", anything else means "show me the
empty form".

`login(request, user)` writes the user's id into the session so they do not have to log in
immediately after signing up.

## 5.4 How `request.user` gets there

```
1.  Browser sends the sessionid cookie
2.  SessionMiddleware      loads that session row from the database
3.  AuthenticationMiddleware  reads _auth_user_id out of it
4.  request.user           a lazy object; the User row is fetched on first access
5.  Nobody logged in?      request.user is AnonymousUser
```

`AnonymousUser` is why `request.user.is_authenticated` never raises `AttributeError`. There is
always a user object; sometimes it is a placeholder that answers `False` to everything.

In templates, `user` and `perms` are always available, from the auth context processor. You
never pass them.

```html
{% if user.is_authenticated %}
    <li><a href="{% url 'blog:dashboard' %}">Desk</a></li>
{% else %}
    <li><a href="{% url 'login' %}">Log in</a></li>
{% endif %}
```

## 5.5 Passwords

Django never stores a password. It stores a hash, by default PBKDF2 with a per-user salt and
several hundred thousand iterations.

```python
user.set_password('raw text')     # hashes it
user.check_password('raw text')   # compares hashes
user.password = 'raw text'        # WRONG — stores the literal string, login breaks
```

Assigning to `.password` directly is a real bug that shows up in seed scripts. This project's
seed command gets it right:

```python
if created:
    user.set_password(DEMO_PASSWORD)
    user.save(update_fields=['password'])
```

`AUTH_PASSWORD_VALIDATORS` in settings rejects passwords that are too short, too common, all
numeric, or too similar to the username. They run in the form, not the model, so
`create_user()` in a script bypasses them — which is fine for seeded demo accounts and not
fine for a real signup path.

## 5.6 `next`

```html
<a href="{% url 'login' %}?next={{ request.path }}">Log in</a>
```

```html
<input type="hidden" name="next" value="{{ next }}">
```

The GET carries the destination into the login page; the hidden field carries it through the
POST. Without the hidden field, a user who was sent to log in from an article lands on the
home page instead and has to find their way back.

Django validates the target is on your own host before redirecting, so this cannot be turned
into an open redirect.

```python
def test_next_sends_you_back_where_you_came_from(self):
    target = reverse('blog:dashboard')
    response = self.client.post(
        f'{reverse("login")}?next={target}',
        {'username': 'regular', 'password': 'testpass123', 'next': target},
    )
    self.assertRedirects(response, target)
```

---

# Part 6 — Authorisation: what may you do

This is the chapter the project was really built for.

## 6.1 Permissions

A permission is a row in `auth_permission` with a codename, a human label and a link to a
content type (a model). Django creates four for every model automatically, at migration time:

```
add_post      change_post      delete_post      view_post
add_comment   change_comment   delete_comment   view_comment
add_category  change_category  delete_category  view_category
```

The full label is `app_label.codename`, e.g. `blog.change_post`. That is what you pass to
`has_perm`.

```python
user.has_perm('blog.change_post')       # True / False
user.get_all_permissions()              # a set of every label
```

Two things to know. Permissions are cached on the user object for the life of the request —
change them in the same request and you must re-fetch the user to see it. And a superuser
returns `True` for everything without a database lookup.

## 6.2 Custom permissions

The four automatic ones cannot express "may publish", because publishing is not adding,
changing, deleting or viewing. So you declare your own:

```python
class Post(models.Model):
    ...
    class Meta:
        ordering = ['-published_at', '-created_at']
        permissions = [
            ('can_publish_post', 'Can publish or unpublish any post'),
        ]


class Comment(models.Model):
    ...
    class Meta:
        ordering = ['created_at']
        permissions = [
            ('can_moderate_comment', "Can hide or delete anyone's comment"),
        ]
```

The tuple is `(codename, human-readable name)`. The second half shows up in the admin's
permission picker, so write it for the person choosing, not for yourself.

**Custom permissions need a migration.** They are database rows, not code:

```bash
python manage.py makemigrations blog
```

```python
migrations.AlterModelOptions(
    name='post',
    options={
        'ordering': ['-published_at', '-created_at'],
        'permissions': [('can_publish_post', 'Can publish or unpublish any post')],
    },
),
```

`AlterModelOptions` changes no columns — it exists so the `post_migrate` signal that creates
permission rows knows about the new one. Forget the migration and `has_perm` silently returns
`False` for everybody, which is a confusing hour.

> Codename convention: Django's own are `verb_model`. Custom ones read better with a `can_`
> prefix (`can_publish_post`) so a glance at a permission list separates yours from the
> generated four.

## 6.3 Groups

Assigning permissions to individual users does not scale and cannot be audited. A **Group** is
a named bundle of permissions; you put the user in the group.

This project keeps the definition in code, not in the admin:

```python
# blog/roles.py — the whole file, abridged only in the comments

_COMMENTING = [
    'blog.view_post',
    'blog.view_comment',
    'blog.add_comment',
    'blog.delete_comment',
]

_WRITING = [
    'blog.add_post',
    'blog.change_post',
    'blog.delete_post',
]

ROLES = {
    'Readers': _COMMENTING,

    'Authors': _COMMENTING + _WRITING,

    'Editors': _COMMENTING + _WRITING + [
        'blog.can_publish_post',
        'blog.can_moderate_comment',
        'blog.change_comment',
        'blog.add_category',
        'blog.change_category',
        'blog.view_category',
    ],
}

DEFAULT_ROLE = 'Authors'
```

Why a file rather than clicking in the admin:

**It is reviewable.** A pull request that widens a role is visible. A checkbox someone ticked
in production at 2am is not.

**It is reproducible.** A new developer runs one command and has the same permissions as
production. Nobody has to remember what to click.

**It is diffable.** "When did Readers get delete rights?" is a `git log` away.

And the command that applies it:

```python
# blog/management/commands/sync_roles.py — the core of handle()
for role, labels in ROLES.items():
    group, created = Group.objects.get_or_create(name=role)

    wanted = []
    for label in labels:
        app_label, codename = label.split('.', 1)
        permission = Permission.objects.filter(
            content_type__app_label=app_label, codename=codename
        ).first()
        if permission is None:
            self.stderr.write(self.style.ERROR(f'  unknown permission: {label}'))
            continue
        wanted.append(permission)

    group.permissions.add(*wanted)
    if options['prune']:
        extra = group.permissions.exclude(pk__in=[p.pk for p in wanted])
        group.permissions.remove(*extra)
```

```bash
python manage.py sync_roles           # idempotent, run it as often as you like
python manage.py sync_roles --prune   # also remove permissions roles.py no longer lists
```

The `permission is None` branch is deliberate. A typo in `roles.py`, or a custom permission
whose migration has not been run, would otherwise silently produce a group with fewer rights
than you think it has. Loud is better.

`--prune` is off by default because removing permissions is the dangerous direction: run it
by accident against a group somebody extended by hand and you take away access with no
warning. Opt in.

## 6.4 Enforcing it in views

Three tools, three jobs.

**`@login_required`** — are you anybody at all? Anonymous users are redirected to `LOGIN_URL`
with `?next=` set.

```python
@login_required
def dashboard(request):
    ...
```

**`@permission_required`** — do you hold this permission?

```python
@login_required
@permission_required('blog.add_post', raise_exception=True)
def post_create(request):
    ...
```

`raise_exception=True` matters. Without it, a logged-in user who lacks the permission is
*redirected to the login page* — where they are already logged in — and the loop looks like a
bug. With it they get a 403 and the custom `403.html`, which is the truth: you are signed in,
you just may not.

**`@require_POST`** — is this the right HTTP method? Anything else gets 405.

```python
@login_required
@require_POST
def post_publish(request, slug):
    ...
```

Decorators apply bottom-up, so order occasionally matters. Put `@login_required` outermost so
an anonymous request is redirected before any other check runs.

## 6.5 `perms` in templates

```html
{% if perms.blog.add_post %}
    <li><a href="{% url 'blog:post_create' %}">Write</a></li>
{% endif %}
```

`perms` is a lazy object from the auth context processor. `perms.blog.add_post` is
`user.has_perm('blog.add_post')`.

> **Hiding a button is not security.** It is courtesy — it stops people clicking things that
> will fail. The check in the view is the security. `curl` has never once been stopped by a
> missing button. Every template check in this project has a matching view check, and the view
> check is the one that counts.

## 6.6 Permission gates the verb; ownership gates the row

Here is the limitation that shapes the rest of this project.

`blog.change_post` means *you are the kind of account that edits posts*. It says nothing about
**which** posts. Django's permission system is model-wide by design. But the rule we want is:

> An author may edit their own work and nobody else's. An editor may edit anything.

That is a per-row question, and no decorator can answer it, because decorators run before the
row is fetched. So the rule lives on the model, where the view and the template can both ask
the same object the same question:

```python
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
```

Read the last line of each: **both halves are required**. The permission (you edit posts) and
the ownership (this one is yours). Drop either and the rule breaks in a different direction.

In the view:

```python
@login_required
def post_edit(request, slug):
    post = get_object_or_404(Post.objects.visible_to(request.user), slug=slug)
    if not post.is_editable_by(request.user):
        raise PermissionDenied('This is not your post.')
```

In the template:

```html
{% if can_edit %}
    <a class="btn btn--small btn--ghost" href="{% url 'blog:post_edit' post.slug %}">Edit</a>
{% endif %}
```

with the view putting the same answer in the context:

```python
'can_edit': post.is_editable_by(request.user),
'can_delete': post.is_deletable_by(request.user),
```

One definition. The button and the check cannot disagree, because they call the same method.
Copy the condition into the template instead and you have created the bug where the button is
hidden but the URL still works, or worse, the button shows and the save 403s.

The same shape appears on `Comment`:

```python
def is_deletable_by(self, user):
    if not user.is_authenticated:
        return False
    return (
        user.is_superuser
        or user.has_perm('blog.can_moderate_comment')
        or self.author_id == user.pk
    )
```

Note `self.author_id == user.pk` rather than `self.author == user`. Comparing the ids avoids
a database query to fetch the author object you do not otherwise need.

## 6.7 403 versus 404

A permission failure has two possible answers and the choice is a security decision.

**403 Forbidden** — "this exists, and you may not." Correct when the user already knows the
thing exists. Editing a post you can see: you know it is there, you clicked it. 403.

**404 Not Found** — "as far as you are concerned, there is nothing here." Correct when the
existence of the thing is itself private.

A draft is the second case. Return 403 for someone else's draft and you have confirmed that
`/post/our-acquisition-of-acme/` is a real URL. The title alone is the leak. So:

```python
post = get_object_or_404(
    Post.objects.with_related().visible_to(request.user), slug=slug
)
```

The filtering happens **inside the queryset**, so a draft you may not see is not "found and
rejected" — it was never in the result set. There is no branch to forget.

```python
def test_a_different_author_gets_404(self):
    self.client.force_login(self.other_author)
    self.assertEqual(self.client.get(self.url()).status_code, 404)
```

## 6.8 A signal for the default role

A new account with no group has no permissions and cannot even comment. Something has to put
them in one.

```python
# blog/signals.py
@receiver(post_save, sender=settings.AUTH_USER_MODEL, dispatch_uid='blog.default_role')
def give_new_user_the_default_role(sender, instance, created, **kwargs):
    if not created or instance.is_superuser:
        return
    group = Group.objects.filter(name=DEFAULT_ROLE).first()
    if group is not None:
        instance.groups.add(group)
```

```python
# blog/apps.py — the whole file
from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blog'
    verbose_name = 'Blog'

    def ready(self):
        from . import signals  # noqa: F401
```

Four details worth copying:

**`if not created`** — `post_save` fires on every save, including updates. Without this guard,
every profile edit re-adds the group, and worse, undoes a deliberate demotion.

**`is_superuser` skipped** — a superuser has everything already; putting them in a group is
noise.

**`.filter(...).first()` not `.get(...)`** — on a fresh database `createsuperuser` may run
before `sync_roles`. `get()` would raise and break account creation entirely. A missing group
here should be a no-op, not a crash.

**`dispatch_uid`** — guarantees the receiver connects once even if the module gets imported
twice. Duplicate signal handlers are a classic "why did that happen three times".

And `ready()` is the only reason `signals.py` is ever imported. The `@receiver` decorator only
connects when the module runs, and nothing else imports it. Keep `ready()` cheap and never
query the database from it — it runs before migrations, when the tables may not exist.

## 6.9 The permission matrix

What each role can actually do in this project:

| Action | Anonymous | Reader | Author | Editor | Superuser |
| --- | --- | --- | --- | --- | --- |
| Read published posts | yes | yes | yes | yes | yes |
| Comment | no | yes | yes | yes | yes |
| Delete own comment | no | yes | yes | yes | yes |
| Delete anyone's comment | no | no | no | yes | yes |
| Hide/restore a comment | no | no | no | yes | yes |
| Write a post | no | no | yes | yes | yes |
| Edit own post | no | no | yes | yes | yes |
| Edit anyone's post | no | no | no | yes | yes |
| Publish own draft | no | no | yes | yes | yes |
| Publish anyone's draft | no | no | no | yes | yes |
| See own drafts | no | no | yes | yes | yes |
| See anyone's drafts | no | no | no | yes | yes |
| Reach `/admin/` | no | no | no | no* | yes |

*Editors need `is_staff` as well to reach the admin — group membership alone does not grant
admin access.

The three rows that read "own ... yes / anyone's ... no" are exactly the ones no decorator can
express. They are the `is_editable_by` rules.
---

# Part 7 — Drafts and publishing

Every post is either a **draft** or **published**. A draft is visible to its author and to the
editors, and to nobody else — not on the front page, not in search, not at its own URL.

## 7.1 TextChoices

```python
class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'

    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.DRAFT
    )
```

`TextChoices` is an enum whose members are `(value, label)`. What you get for those three
lines:

```python
Post.Status.DRAFT            # 'draft'          — use this, never the raw string
Post.Status.DRAFT.label      # 'Draft'
Post.Status.choices          # [('draft', 'Draft'), ('published', 'Published')]
post.get_status_display()    # 'Draft'          — Django generates this method
```

A form field built from `choices` renders as a `<select>` and rejects anything not in the
list, so a crafted POST cannot set `status='deleted'`.

Use `Post.Status.PUBLISHED` everywhere and never the literal `'published'`. Typos in string
literals fail silently — the filter simply matches nothing — while a typo in an enum attribute
is an `AttributeError` the first time it runs.

The default is `DRAFT`, which is the safe direction: a post that half-saved because of a crash
is invisible rather than accidentally live.

## 7.2 `published_at`, and the rule about when it moves

```python
published_at = models.DateTimeField(null=True, blank=True)
created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)
```

Three dates, three meanings:

| Field | Set when | Means |
| --- | --- | --- |
| `created_at` | insert, automatically | when it was started |
| `updated_at` | every save, automatically | when it was last touched |
| `published_at` | by our code | when it went live, or NULL if it has not |

The rule lives in `save()`:

```python
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
```

The `is None` guard is the whole point. Without it, every save of a published post would move
the date, and fixing a typo three weeks later would drag the article back to the top of the
front page. Two tests pin this down:

```python
def test_the_date_does_not_move_when_you_fix_a_typo(self):
    original = self.post.published_at
    self.post.title = 'A published piece, corrected'
    self.post.save()
    self.post.refresh_from_db()
    self.assertEqual(self.post.published_at, original)

def test_unpublishing_clears_the_date(self):
    post = Post.objects.create(title='Briefly live', content='x',
                               author=self.author, status=Post.Status.PUBLISHED)
    post.status = Post.Status.DRAFT
    post.save()
    self.assertIsNone(post.published_at)
```

> Always `timezone.now()`, never `datetime.now()`. With `USE_TZ = True` the former is
> timezone-aware and the latter is not, and mixing them raises warnings that turn into wrong
> comparisons.

## 7.3 A custom QuerySet

The filter "published" now has to appear in the front page, the archive, the section pages,
the related-posts strip and the counts. Written out five times, it will be wrong in at least
one of them within a month.

```python
class PostQuerySet(models.QuerySet):
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
        if user.is_authenticated:
            if user.is_superuser or user.has_perm('blog.can_publish_post'):
                return self
            return self.filter(
                models.Q(status=Post.Status.PUBLISHED, published_at__lte=timezone.now())
                | models.Q(author=user)
            )
        return self.published()
```

Because every method returns a queryset, they **chain**:

```python
Post.objects.published().with_related().search('cache')
Post.published.with_related().filter(category=section)
Post.objects.visible_to(request.user).drafts()
```

Note `published_at__lte=timezone.now()` in `published()`. It is not decoration: it means a
post whose publication date is in the future is not public yet. Scheduled publishing is
therefore already supported by the data model — all that is missing is a form field to set
the date. There is a test for it:

```python
def test_a_future_dated_post_is_not_published_yet(self):
    post = Post.objects.create(title='Tomorrow', content='x',
                               author=self.author, status=Post.Status.PUBLISHED)
    Post.objects.filter(pk=post.pk).update(
        published_at=timezone.now() + timezone.timedelta(days=1)
    )
    self.assertNotIn(post, Post.published.all())
```

## 7.4 Two managers

```python
class PublishedManager(models.Manager.from_queryset(PostQuerySet)):
    """`Post.published` — the public site's front door."""

    def get_queryset(self):
        return super().get_queryset().published()


class Post(models.Model):
    ...
    objects = PostQuerySet.as_manager()
    published = PublishedManager()
```

| Expression | Returns |
| --- | --- |
| `Post.objects.all()` | everything, drafts included |
| `Post.objects.drafts()` | drafts only |
| `Post.objects.visible_to(user)` | published, plus that user's own drafts |
| `Post.published.all()` | published only |
| `Post.published.with_related()` | published, with the joins |

Two subtleties that cost people an afternoon each.

**`from_queryset` versus a plain Manager subclass.** Write `class PublishedManager(models.Manager)`
and `Post.published.with_related()` raises `AttributeError` — a Manager only exposes its own
methods, not the queryset's. `Manager.from_queryset(PostQuerySet)` copies every queryset
method onto the manager. `QuerySet.as_manager()` does the same thing for the simple case.

**The first manager declared is the default.** `Post._default_manager` is whichever is listed
first, and that is what the admin uses, what related managers (`category.posts`) use, and what
`get_object_or_404` reaches for when handed a model class. Put a filtered manager first and
your admin quietly stops showing drafts. So `objects` is declared first, unfiltered, always.

## 7.5 Changing a live table: the three-step migration

This is the part most tutorials skip, and the part that matters on any project with users.

Adding `status`, `published_at` and `updated_at` to `Post`, and replacing `Comment.name` with
`Comment.author`, cannot be done in one migration on a table that already has rows. A
`NOT NULL` column added to a table full of existing rows has nothing to put in it. A `UNIQUE`
index on a column full of empty strings fails on the second row.

The pattern is **add loose, backfill, tighten**, and it is three migrations.

### 0009 — add, with everything nullable or defaulted

```python
operations = [
    migrations.AddField(
        model_name='category',
        name='slug',
        field=models.SlugField(blank=True, default='', max_length=64),   # not unique yet
        preserve_default=False,
    ),
    migrations.AddField(
        model_name='post',
        name='status',
        field=models.CharField(
            choices=[('draft', 'Draft'), ('published', 'Published')],
            default='draft', max_length=10,
        ),
    ),
    migrations.AddField(
        model_name='post',
        name='published_at',
        field=models.DateTimeField(blank=True, null=True),
    ),
    migrations.AddField(
        model_name='post',
        name='updated_at',
        # auto_now cannot invent a value for rows that already exist, so
        # this one-off default fills them and is then dropped.
        field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
        preserve_default=False,
    ),
    migrations.AlterField(
        model_name='post',
        name='content',
        # Was TextField(max_length=100), which silently capped every
        # article at 100 characters in the form layer.
        field=models.TextField(),
    ),
    migrations.AddField(
        model_name='comment',
        name='author',
        # Nullable for now: 0010 fills it, 0011 makes it required.
        field=models.ForeignKey(
            null=True, on_delete=django.db.models.deletion.CASCADE,
            related_name='comments', to=settings.AUTH_USER_MODEL,
        ),
    ),
]
```

Nothing here can fail. Every new column is nullable or has a default; no old column is
removed. `preserve_default=False` means "use this default for the existing rows, then forget
it" — the model itself has no default.

### 0010 — a data migration

No schema changes at all. It only moves values.

```python
from django.conf import settings
from django.db import migrations
from django.utils.text import slugify


def forwards(apps, schema_editor):
    Category = apps.get_model('blog', 'Category')
    Post = apps.get_model('blog', 'Post')
    Comment = apps.get_model('blog', 'Comment')
    User = apps.get_model(settings.AUTH_USER_MODEL)

    # one category per name, each with a slug
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

    # everything that existed before this migration was already live
    Post.objects.update(status='published')
    for post in Post.objects.all():
        Post.objects.filter(pk=post.pk).update(published_at=post.created_at)

    # comments were signed with a free-text name. Turn each distinct name
    # into an inactive account so the FK in 0011 has something to point at.
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
                username=username, email='', password='!', is_active=False,
            )
            by_name[raw.lower()] = user
        comment.author = user
        comment.save(update_fields=['author'])


class Migration(migrations.Migration):
    dependencies = [('blog', '0009_publishing_and_signed_comments')]
    operations = [migrations.RunPython(forwards, backwards)]
```

**`apps.get_model()`, never a direct import.** This is the rule of data migrations. `apps` is
a *historical* registry: `apps.get_model('blog', 'Comment')` gives you the model as it existed
at this point in history, with `name` still present and `author` still nullable. Import the
real `blog.models.Comment` and this file breaks the day you rename a field, because it would
be describing a model from the future.

Historical models have no custom methods either — no `save()` override, no properties. That is
why the slug logic is inlined rather than calling `Category.save()`.

**`password='!'`** is Django's marker for an unusable password. Those generated accounts exist
so the foreign key has a target; nobody can log into them.

**`RunPython(forwards, backwards)`** — the second argument is the reverse. Supplying one makes
the migration reversible; `migrations.RunPython.noop` is the honest answer when there is
nothing to undo.

### 0011 — tighten

```python
operations = [
    migrations.AlterField(
        model_name='category', name='name',
        field=models.CharField(max_length=54, unique=True),
    ),
    migrations.AlterField(
        model_name='category', name='slug',
        field=models.SlugField(blank=True, max_length=64, unique=True),
    ),
    migrations.AlterField(
        model_name='comment', name='author',
        field=models.ForeignKey(
            on_delete=django.db.models.deletion.CASCADE,
            related_name='comments', to=settings.AUTH_USER_MODEL,
        ),
    ),
    migrations.RemoveField(model_name='comment', name='name'),

    migrations.AlterModelOptions(
        name='post',
        options={
            'ordering': ['-published_at', '-created_at'],
            'permissions': [('can_publish_post', 'Can publish or unpublish any post')],
        },
    ),
    migrations.AddIndex(
        model_name='post',
        index=models.Index(fields=['-published_at'], name='post_published_at_idx'),
    ),
]
```

Every operation here would have crashed before 0010 ran: a unique index on a column full of
empty strings, a NOT NULL on a column full of nulls. Order is the whole trick.

`RemoveField` is last and is the irreversible one. Once it runs, the free-text `name` is gone
for good — which is precisely why 0010 turned it into a real account first.

### Verifying hand-written migrations

Migrations can be written by hand; the risk is that they drift from the models. One command
settles it:

```bash
python manage.py makemigrations blog --check --dry-run --noinput
```

"No changes detected" means the migration files and the models describe exactly the same
schema. Put it in CI.

> On a large production table there is more to it than ordering: take a `lock_timeout` before
> schema changes, and build indexes with `CONCURRENTLY` (Django ships
> `AddIndexConcurrently` for Postgres, which needs `atomic = False` on the migration class).
> SQLite, which this project uses, rewrites the whole table for most `ALTER`s and does not
> care — which is exactly why habits formed on SQLite hurt later.

## 7.6 The publish toggle

```python
@login_required
@require_POST
def post_publish(request, slug):
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
```

`@require_POST` means the toggle needs a form with a CSRF token and cannot be fired by an
`<img src>` on somebody else's page. The `next` field lets the same view serve the article
page and the dashboard, returning you to whichever you came from.

`post.save()` — not `queryset.update()` — because we *want* the model's `save()` to run and
manage `published_at`.

```html
<form method="post" action="{% url 'blog:post_publish' post.slug %}" class="inline-form">
    {% csrf_token %}
    <input type="hidden" name="next" value="{% url 'blog:dashboard' %}">
    <button class="linkish" type="submit">{% if post.is_published %}Unpublish{% else %}Publish{% endif %}</button>
</form>
```

## 7.7 The dashboard

```python
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

    if request.user.has_perm('blog.can_publish_post'):
        context['review_queue'] = (
            Post.objects.drafts().with_related().exclude(author=request.user)
        )
    if request.user.has_perm('blog.can_moderate_comment'):
        context['hidden_comments'] = (
            Comment.objects.filter(is_approved=False).select_related('post', 'author')
        )

    return render(request, 'blog/dashboard.html', context)
```

Note `Post.objects` here, not `Post.published` — this is the one page that is *supposed* to
show you your drafts.

The two conditional keys are a nice template pattern: for an author, `review_queue` is simply
absent from the context, and a missing variable in a Django template is falsy rather than an
error. So the template needs no permission check of its own:

```html
{% if review_queue %}
    <div class="section-rule"><h2 class="kicker">Drafts by other people</h2></div>
    ...
{% endif %}
```

---

# Part 8 — Comments that require an account

The original comment model had a free-text `name` field. Anyone could type anything, including
somebody else's name.

## 8.1 Delete the field, do not validate it

```python
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name='comments')
    content = models.TextField()
    is_approved = models.BooleanField(default=True)
```

```python
class CommentForm(StyledForm):
    """No name field any more.

    The commenter is `request.user`, set in the view. A field the browser can
    send is a field the browser can lie about, so identity never travels
    through the form.
    """

    class Meta:
        model = Comment
        fields = ['content']
```

The form has one field. There is no validation to write, no impersonation check to remember,
no admin setting to get wrong. The attack surface was removed rather than defended.

```python
def test_the_comment_form_has_no_identity_field(self):
    self.assertEqual(list(CommentForm().fields), ['content'])
```

## 8.2 The view

```python
def post_detail(request, slug):
    post = get_object_or_404(
        Post.objects.with_related().visible_to(request.user), slug=slug
    )

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.info(request, 'Log in to leave a comment.')
            return redirect_to_login(request.get_full_path())

        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            messages.success(request, 'Comment posted.')
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
```

The view is **not** decorated with `@login_required`, and that is deliberate: reading an
article must work when logged out. Only the POST branch requires an account.

`redirect_to_login(request.get_full_path())` sends them to the login page with `?next=` set to
the article they were reading, so after logging in they land back where they were instead of
on the home page.

```python
def test_anonymous_post_is_bounced_to_the_login_page(self):
    response = self.client.post(self.url(), {'content': 'Sneaking one in'})
    self.assertEqual(response.status_code, 302)
    self.assertIn(reverse('login'), response.url)
    self.assertEqual(Comment.objects.count(), 0)
```

The last assertion is the one that matters. A redirect is nice; not creating the comment is
the requirement.

## 8.3 The template

```html
{% if user.is_authenticated %}
    <form class="form" method="post" novalidate>
        {% csrf_token %}
        <p class="kicker">Leave a comment as <strong>{{ user.username }}</strong></p>
        {% for field in form %}
            {% include 'blog/partials/_field.html' %}
        {% endfor %}
        <button class="btn" type="submit">Post comment</button>
    </form>
{% else %}
    <p class="empty">
        Comments are signed here — no drive-by anonymous takes.
        <a href="{% url 'login' %}?next={{ request.path }}">Log in</a>
        or <a href="{% url 'register' %}">make an account</a> to join in.
    </p>
{% endif %}
```

Showing the reason rather than an empty space is worth the extra line. "You must be logged in"
with no link is the most common bad version of this.

## 8.4 Moderation

```python
is_approved = models.BooleanField(
    default=True,
    help_text='Untick to hide the comment from everyone except its author.',
)
```

Default `True`, so comments appear immediately — pre-moderation on a small site means comments
that never appear. Hiding is the exception, not the gate.

```python
class CommentQuerySet(models.QuerySet):
    def visible_to(self, user):
        """Approved comments, plus your own while they are hidden."""
        if user.is_authenticated:
            if user.is_superuser or user.has_perm('blog.can_moderate_comment'):
                return self
            return self.filter(models.Q(is_approved=True) | models.Q(author=user))
        return self.filter(is_approved=True)
```

Letting an author still see their own hidden comment is a deliberate choice: they see it
greyed out and labelled, instead of it vanishing and them posting it again. Two tests hold
that shape:

```python
def test_a_hidden_comment_is_invisible_to_other_readers(self): ...
def test_a_hidden_comment_is_still_visible_to_its_author(self): ...
```

```python
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
    ...
```

Note the difference. Deleting uses the **model method**, because "your own, or a moderator" is
a per-row rule. Hiding uses the **decorator**, because hiding is a moderator-only verb with no
ownership component. Right tool, right question.

`save(update_fields=[...])` writes two columns instead of every column. On a wide table that
matters, and it also avoids clobbering a field another request changed in between.

---

# Part 9 — The views, one by one

Ten views, all function-based. Class-based views would be shorter for the list pages and
longer to explain; for teaching, a function you can read top to bottom wins.

## 9.1 Two shared helpers

```python
def sections():
    """Categories that actually have something published in them."""
    return Category.objects.annotate(
        post_count=Count(
            'posts',
            filter=Q(
                posts__status=Post.Status.PUBLISHED,
                posts__published_at__lte=timezone.now(),
            ),
        )
    ).filter(post_count__gt=0)
```

`Count('posts', filter=Q(...))` is a **conditional aggregate**: one query that counts only the
matching rows. The naive version — fetch all categories, loop, call `.count()` on each — is
one query per category and would also count drafts, putting a "Django (7)" chip on a section
with four public articles.

`.filter(post_count__gt=0)` filters on the annotation, which becomes a `HAVING` clause. You
cannot do that in the same `filter()` call that defined it; annotate first, then filter.

```python
def paginate(request, queryset, per_page=PAGE_SIZE):
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get('page'))
```

`get_page()` rather than `page()`: it clamps out-of-range numbers and tolerates `None` and
garbage instead of raising. `?page=banana` gives you page 1, not a 500.

Paginator only ever pulls one page out of the database — `page.object_list` is a
`LIMIT`/`OFFSET` query, not the whole table sliced in Python.

## 9.2 Reading

```python
def index(request):
    posts = list(Post.published.with_related()[:7])
    lead, rest = (posts[0], posts[1:]) if posts else (None, [])
    return render(request, 'blog/home.html', {
        'lead': lead,
        'posts': rest,
        'categories': sections(),
        'total': Post.published.count(),
    })
```

One `list()` call, one query, seven rows: the lead story and the six cards under it. Slicing
before evaluating means the `LIMIT` reaches the database rather than seven hundred rows
reaching Python.

```python
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
```

`request.GET.get('q', '')` with a default, never `request.GET['q']` — the key is absent on the
first visit and the bracket form raises `MultiValueDictKeyError`.

The `slug.isdigit()` branch is a real-world touch: the section links used to be
`?category=<pk>` and somebody has that URL bookmarked. Six lines to not break it.

`total` comes from `page.paginator.count`, which is a `COUNT(*)` over the whole filtered set —
not `len(posts)`, which would only count the nine on this page.

```python
def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    page = paginate(request, Post.published.with_related().filter(category=category))
    return render(request, 'blog/category_detail.html', {
        'category': category,
        'page': page,
        'posts': page.object_list,
        'total': page.paginator.count,
    })
```

`get_object_or_404(Model, **kwargs)` is `Model.objects.get()` that raises `Http404` instead of
`DoesNotExist`. Use it in every detail view. Writing `try/except DoesNotExist` by hand is four
lines that do the same thing, plus one place to forget.

It also takes a queryset, which is how the draft rule gets enforced:

```python
post = get_object_or_404(Post.objects.with_related().visible_to(request.user), slug=slug)
```

## 9.3 Writing

```python
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
```

`redirect(post)` works because `Post` has `get_absolute_url()`.

> A bug this code used to have: `form.save(commit=False)` followed by `form.save()` instead of
> `post.save()`. It happens to work — `form.save()` saves `form.instance`, which is the same
> object — but it reads as though the author assignment is being thrown away, and the day
> somebody adds a line between them it stops being a coincidence.

`post_edit` and `post_create` render the **same template**, with the heading and button label
passed in:

```python
return render(request, 'blog/post_form.html', {
    'form': form, 'post': post,
    'heading': 'Edit post', 'submit_label': 'Update', ...
})
```

Two templates that differ by one word will drift apart. One template with two callers cannot.

## 9.4 Deleting, in two steps

```python
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
```

GET renders a confirmation; POST performs the deletion. This is not politeness, it is
correctness: `GET` is defined as *safe* in HTTP, and crawlers, prefetchers, antivirus
scanners and email link-checkers all act on that definition. A delete link behind a GET will
eventually be clicked by a robot.

`title` is captured **before** `delete()`, because afterwards the instance is a shell.

```python
def test_deleting_shows_a_confirmation_page_before_it_deletes(self):
    self.client.force_login(self.author)
    url = reverse('blog:post_delete', kwargs={'slug': self.post.slug})
    self.assertContains(self.client.get(url), 'Yes, delete it')
    self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())
```

## 9.5 Messages

`django.contrib.messages` stores a short list of strings in the session, shows them on the
next page, and deletes them.

```python
messages.success(request, 'Comment posted.')
messages.warning(request, 'Comment deleted.')
messages.info(request, 'Log in to leave a comment.')
messages.error(request, 'Something went wrong.')
```

Rendered once, in `base.html`, so every view gets it free:

```html
{% if messages %}
    <div class="shell messages" role="status">
        {% for message in messages %}
            <p class="message message--{{ message.tags|default:'info' }}">{{ message }}</p>
        {% endfor %}
    </div>
{% endif %}
```

`message.tags` is `success` / `warning` / `info` / `error`, which the CSS turns into the
coloured left border. `role="status"` makes a screen reader announce it.

Messages pair with redirects: you add one before a `redirect()` and the *next* page shows it.
That is the whole point — a message survives exactly one redirect, which is what makes
POST-Redirect-GET feel responsive.

---

# Part 10 — Templates in depth

## 10.1 The files

```
templates/
├── base.html                    the frame: masthead, nav, messages, footer
├── 403.html, 404.html           error pages, used when DEBUG = False
├── registration/
│   ├── login.html               LoginView looks here by name
│   └── register.html
└── blog/
    ├── home.html                lead story + cards + sections
    ├── post_list.html           archive: search, filter, pagination
    ├── category_detail.html     one section
    ├── post_detail.html         article, comments, related
    ├── post_form.html           create AND edit
    ├── post_confirm_delete.html the confirmation step
    ├── dashboard.html           the desk
    ├── about.html
    └── partials/
        ├── _card.html           one post card
        ├── _comment.html        one comment, with its moderation buttons
        ├── _field.html          one form field, label + errors + help
        ├── _pagination.html     newer / older
        └── _recent.html         rendered by the recent_posts inclusion tag
```

The leading underscore on partials is a convention, not a rule. It says "this is not a page,
do not render it directly".

## 10.2 Custom template tags

Templates deliberately cannot call functions with arguments. When a template needs something
that depends on the request, or takes parameters, that is what a tag library is for.

Three things must be true or `{% load %}` fails:

1. the module lives in an app that is in `INSTALLED_APPS`
2. it is inside a `templatetags/` package **with an `__init__.py`**
3. the template says `{% load blog_extras %}` — in every file that uses it

> And restart the dev server after creating one. The tag registry is built at startup and
> does not autoreload. This costs everybody twenty minutes exactly once.

```python
# blog/templatetags/blog_extras.py
from django import template
from ..models import Post

register = template.Library()
```

### `query_string` — the pagination fix

```python
@register.simple_tag(takes_context=True)
def query_string(context, **kwargs):
    """Rebuild the current querystring with a few keys changed.

        {% query_string page=3 %}    ->  ?q=django&category=web&page=3
        {% query_string page=None %} ->  ?q=django&category=web
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
```

The bug this exists to prevent: search for something, get four pages of results, click "page
2", and the search term is gone because the link was `?page=2`. Nearly every hand-rolled
pagination has it.

`request.GET` is immutable, hence `.copy()`. `takes_context=True` is what gives the tag access
to the request, which is only in the context because of the `request` context processor.

```html
<a class="pagination__step" href="{% query_string page=page.next_page_number %}">Older →</a>
```

```html
<a class="chip" href="{% query_string category=category.slug page=None %}">
```

Changing the section resets the page — otherwise you filter to a section with two articles
while still asking for page four, and get an empty list.

### Filters

```python
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
```

```html
{{ post.author|display_name }}
<span class="comment__mark">{{ comment.author|initials }}</span>
```

A filter is a function of one argument (two with a parameter) that returns a value. Keep them
pure and total: a filter that raises takes the whole page down, so `display_name` handles
`None` and `AnonymousUser` rather than assuming a `User`.

### An inclusion tag

```python
@register.inclusion_tag('blog/partials/_recent.html')
def recent_posts(count=3, exclude=None):
    """Renders a partial instead of returning a string."""
    posts = Post.published.with_related()
    if exclude is not None:
        posts = posts.exclude(pk=exclude.pk)
    return {'posts': posts[:count]}
```

The returned dict becomes the partial's **entire** context — the surrounding page's variables
are not visible inside it. That isolation is the difference from `{% include %}`, which sees
everything.

Use an inclusion tag when the fragment needs data no view fetched. Use `{% include %}` when
the data is already in the loop you are standing in.

## 10.3 Reading the article template

```html
{% extends 'base.html' %}
{% load blog_extras %}

{% block content %}
<div class="shell shell--narrow">

    {% if not post.is_published %}
        <div class="banner">
            <strong>Draft.</strong> Only you and the editors can see this page.
        </div>
    {% endif %}

    <header class="article__head">
        {% if post.category %}
            <p class="kicker kicker--accent">
                <a href="{{ post.category.get_absolute_url }}">{{ post.category.name }}</a>
            </p>
        {% endif %}

        <h1 class="article__title">{{ post.title }}</h1>

        <p class="article__byline">
            <span class="meta">By {{ post.author|display_name }}</span>
            <span class="dot">·</span>
            <span class="meta">{{ post.published_at|default:post.created_at|date:"j F Y" }}</span>
            <span class="dot">·</span>
            <span class="meta">{{ post.reading_time }} min read</span>
        </p>

        {% if can_edit or can_delete %}
            <p class="toolbar"> ... edit / publish / delete ... </p>
        {% endif %}
    </header>

    <div class="prose">{{ post.content|linebreaks }}</div>
    ...
```

Points worth noticing:

`{% if post.category %}` — the FK is `null=True`, so it can genuinely be missing. Guard every
nullable relation before you dot into it.

`published_at|default:created_at` — a draft has no publication date, so the byline falls back
rather than printing nothing.

`post.reading_time` and `post.excerpt` are model **properties**, called with no parentheses.
Derived values belong on the model, not in the view and not in the template:

```python
@property
def excerpt(self):
    return Truncator(self.content).chars(190)

@property
def reading_time(self):
    words = len(self.content.split())
    return max(1, round(words / 200))
```

`{{ post.content|linebreaks }}` turns blank lines into paragraphs. The content is still
escaped first — `linebreaks` adds tags, it does not mark the input safe.
---

# Part 11 — Management commands and seeding

## 11.1 Anatomy of a command

`python manage.py <name>` finds `<app>/management/commands/<name>.py`. There is nothing to
register — Django locates it by directory layout. Both `management/` and `commands/` need an
`__init__.py`.

```
blog/
└── management/
    ├── __init__.py
    └── commands/
        ├── __init__.py
        ├── seed_blog.py
        └── sync_roles.py
```

```python
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'What this does. Shown by manage.py help <name>.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='...')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('done'))
```

`add_arguments` receives an `argparse` parser, so you get the whole argparse vocabulary free.

**`self.stdout.write`, not `print`.** It respects `--no-color`, and it is redirectable, which
is what lets a test do `call_command('seed_blog', stdout=StringIO())` and assert on the output
instead of polluting the test run.

**Honour `verbosity`.** Django passes it to every command. Ignoring it is a small rudeness
that becomes a large one when a test calls your command 60 times:

```python
def handle(self, *args, **options):
    quiet = options['verbosity'] == 0
    ...
    if not quiet:
        self.stdout.write(...)
```

## 11.2 The seed command

```python
@transaction.atomic
def handle(self, *args, **options):
    slugs = [slugify(article['title']) for article in ARTICLES]

    if options['purge']:
        deleted, _ = Post.objects.all().delete()
        self.stdout.write(self.style.WARNING(f'Purged all posts ({deleted} rows).'))
    elif options['reset']:
        Post.objects.filter(slug__in=slugs).delete()

    # The groups have to exist before anyone can be put in one.
    call_command('sync_roles', verbosity=0)

    people = self.seed_people(skip=options['skip_users'])
    self.seed_sections()
    self.seed_articles(people)
```

`@transaction.atomic` wraps the whole command in one transaction. If article seven raises,
articles one to six are rolled back too and you are left with an empty database rather than a
half-built one. Seeds should be all or nothing.

`call_command('sync_roles', verbosity=0)` runs one command from another. Better than
duplicating the logic, and it keeps `roles.py` the single source of truth.

### Idempotence

```python
for article in ARTICLES:
    slug = slugify(article['title'])
    if Post.objects.filter(slug=slug).exists():
        self.stdout.write(f'  skip     {slug}')
        continue
```

Running the command twice must not produce twenty articles. `get_or_create` and
`update_or_create` are the other two tools for this:

```python
user, created = User.objects.get_or_create(
    username=person['username'],
    defaults={'first_name': ..., 'last_name': ..., 'email': ...},
)

Category.objects.update_or_create(name=name, defaults={'description': description})
```

The distinction: the lookup arguments identify the row; `defaults` is only applied on create
(`get_or_create`) or on both create and update (`update_or_create`).

### Passwords, and the group that must be replaced

```python
if created:
    user.set_password(DEMO_PASSWORD)
    user.save(update_fields=['password'])

group = Group.objects.filter(name=person['role']).first()
if group:
    # A signal already put new accounts in the default group, so
    # clear it first — otherwise a Reader would keep Author rights.
    user.groups.set([group])
```

`set()` replaces; `add()` appends. This is a genuine interaction bug the signal creates: every
new user is auto-added to **Authors**, so a seeded Reader would be an Author *and* a Reader
and would sail past the permission check the demo exists to show. `set()` fixes it in one
word, and this is the kind of thing that is obvious once and invisible forever after.

### Backdating rows created with `auto_now_add`

```python
post = Post.objects.create(...)

# created_at is auto_now_add, so it can only be corrected afterwards
# — and .update() skips save(), which is what we want here.
Post.objects.filter(pk=post.pk).update(
    created_at=written_at,
    published_at=written_at if post.is_published else None,
)
```

`auto_now_add` overwrites whatever you pass on insert; there is no way to set it directly.
`queryset.update()` issues a plain `UPDATE` that bypasses `save()` and both `auto_now` fields.
That is exactly what a seed script wants, and exactly what application code usually does not.

## 11.3 The data lives in a separate file

```python
# blog/seed_data.py
PEOPLE = [
    {'username': 'aviral', 'first_name': 'Aviral', 'last_name': 'Ale', 'role': 'Editors'},
    ...
]

DEMO_PASSWORD = 'deskpass123'

SECTIONS = {
    'Django': 'The framework, its sharp edges, and the parts of it people never read.',
    ...
}

ARTICLES = [
    {
        'title': 'The N+1 query is the most expensive bug you will never see',
        'category': 'Django',
        'author': 'aviral',
        'status': 'published',
        'days_ago': 4,
        'content': """...""",
    },
    ...
]

COMMENTS = {
    'the-n1-query-is-the-most-expensive-bug-you-will-never-see': [
        ('rohan_dev', 'Found three of these in our admin views...', 3),
        ...
    ],
}
```

Data in one file, logic in another. Adding an article touches no Django code, and the command
stays short enough to read in one sitting. The `COMMENTS` keys are slugs, which match what
`Post.save()` generates from the titles.

One of the ten articles has `'status': 'draft'`, deliberately, so a fresh install can
demonstrate the draft rule without anyone having to create one.

## 11.4 Generated cover art

`blog/covers.py` makes a deterministic two-ink print for each slug with Pillow, so the demo
site has real images without shipping stock photos.

```python
def _seed(slug):
    digest = hashlib.md5(slug.encode('utf-8')).hexdigest()
    return random.Random(int(digest[:12], 16))
```

Seeding the RNG from a hash of the slug is the trick: the same post always gets the same
cover, on every machine, forever, without storing anything.

```python
def make_cover(slug, size=SIZE):
    """Return a PIL image: a two-ink plate printed on aged paper."""
    rnd = _seed(slug)
    img = Image.new('RGB', size, rnd.choice(PAPERS))

    inks = rnd.sample(INKS, 2)
    plates = rnd.sample(COMPOSITIONS, 2)

    for index, (draw_plate, ink) in enumerate(zip(plates, inks)):
        layer = _blank(size)
        # the second plate lands slightly off register, like a real two-pass print
        offset = 0 if index == 0 else rnd.randint(6, 22)
        draw_plate(ImageDraw.Draw(layer), size, ink, rnd, offset, -offset // 2)
        layer = layer.filter(ImageFilter.GaussianBlur(rnd.uniform(0.5, 1.4)))
        img = ImageChops.multiply(img, layer)

    return _vignette(_grain(img, rnd))
```

Not Django, strictly — but it is the answer to "where do the images come from", and
`ImageChops.multiply` is genuinely how two ink plates combine on paper.

---

# Part 12 — Testing

## 12.1 What to test

There is a test in most projects that creates a model, saves it, reads it back, and asserts
the field equals what was set. Delete it. That behaviour belongs to Django, is tested by
Django, and your copy exists only to fail on an upgrade.

**Test the sentence you would say to a colleague, not the mechanism underneath it.** Nobody
says "the ORM persists a CharField". People do say "a draft is invisible to everyone except
its author", and that is a rule *you* invented and can therefore break.

Every test in this project maps to a sentence:

- a draft is not visible to a logged-out visitor, or to a different author
- an editor can see any draft
- publishing stamps the date once and does not move it when you fix a typo
- you cannot comment without an account
- the comment is signed by the session, not by the POST body
- an author edits their own work and nobody else's
- a reader cannot reach the write page
- deleting requires a POST and a confirmation
- two posts with the same title get different URLs
- the front page does not run one query per post

## 12.2 The machinery

```python
class BlogTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('sync_roles', verbosity=0)
        cls.section = Category.objects.create(name='Django')
        cls.author = cls.make_user('author', 'Authors')
        cls.editor = cls.make_user('editor', 'Editors')
        cls.reader = cls.make_user('reader', 'Readers')
        cls.post = Post.objects.create(..., status=Post.Status.PUBLISHED)
        cls.draft = Post.objects.create(..., status=Post.Status.DRAFT)

    @staticmethod
    def make_user(username, role):
        user = User.objects.create_user(username=username, password='testpass123')
        # A post_save signal already put them in the default group, so `set`
        # rather than `add` — otherwise a Reader keeps Author permissions.
        user.groups.set([Group.objects.get(name=role)])
        return user
```

**`TestCase` wraps every test in a transaction and rolls it back.** Tests cannot see each
other's data, and the order they run in does not matter. It also uses a **separate test
database**, created and destroyed around the run — your real data is never touched.

**`setUpTestData` versus `setUp`.** `setUpTestData` runs once per class, inside an outer
transaction rolled back at the end. `setUp` runs before every method. On a class with fifteen
tests that is one set of fixtures instead of fifteen. It is the cheapest speedup available in
a Django suite and most people never learn it exists.

The catch: objects created in `setUpTestData` are shared, so modifying one in a test could
leak. Django guards this by handing each test method its own in-memory copy of those
attributes.

## 12.3 The client

```python
self.client.get(url)
self.client.post(url, {'content': 'hello'})
self.client.force_login(self.reader)
self.client.logout()
```

`force_login` skips password checking and the login form — you are testing the view, not
Django's authentication. Use `client.login(username=..., password=...)` only when the login
flow itself is the subject.

Useful assertions:

| Assertion | Checks |
| --- | --- |
| `assertEqual(response.status_code, 403)` | the status |
| `assertContains(response, 'text')` | 200 **and** the text is present |
| `assertNotContains(response, 'text')` | 200 and it is absent |
| `assertRedirects(response, url)` | it redirected there, and that page loads |
| `assertFormError(form, 'field', 'message')` | a specific validation error |
| `assertNumQueries(n)` | exactly n queries ran |

`assertContains` checking for a 200 first is why it beats `assertIn(text, response.content)` —
a 500 error page containing your search string would pass the naive version.

## 12.4 Reading two of them

```python
class DraftVisibilityTests(BlogTestCase):
    """A draft returns 404, never 403."""

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
```

Four tests, four sentences, four different accounts. `reverse()` rather than a hardcoded path,
so changing the URL pattern does not touch the tests.

```python
class QueryCountTests(BlogTestCase):
    def test_the_front_page_does_not_query_per_post(self):
        for i in range(6):
            Post.objects.create(title=f'Filler {i}', content='word ' * 30,
                                author=self.author, category=self.section,
                                status=Post.Status.PUBLISHED)
        with self.assertNumQueries(3):
            self.client.get(reverse('blog:home'))
```

This is the N+1 tripwire. It fails if someone removes `with_related()` from the front page
view, and the failure message says exactly how many queries ran. You cannot regress a number
nobody is watching.

## 12.5 Naming

`test_draft_is_invisible_to_other_authors` tells you what broke from the failure output alone.
`test_post_detail_2` requires archaeology. The name is the specification; write it as a
sentence.

```bash
python manage.py test                                    # everything
python manage.py test blog                               # one app
python manage.py test blog.tests.DraftVisibilityTests    # one class
python manage.py test blog.tests.CommentTests.test_a_logged_in_reader_can_comment
python manage.py test --parallel                         # use all cores
python manage.py test -v 2                               # name every test as it runs
python manage.py test --failfast                         # stop at the first failure
```

The best habit: **write the test that would have caught the last bug you shipped.** Not a
suite. One test. Do it every time, and in a year the suite is made entirely of things that
actually went wrong — which is the only kind anyone trusts.

---

# Part 13 — Performance

## 13.1 The N+1 problem

```python
posts = Post.objects.all()                     # 1 query
```

```html
{% for post in posts %}
    {{ post.category.name }}                    {# 1 query, per post #}
{% endfor %}
```

Forty posts, forty-one queries. Nothing raises. No test fails. The page simply gets slower
every time the data grows.

```python
posts = Post.objects.select_related('category', 'author')     # 1 query, with JOINs
```

| Tool | Works on | How |
| --- | --- | --- |
| `select_related` | forward FK, OneToOne | a SQL JOIN, one query |
| `prefetch_related` | reverse FK, ManyToMany | a second query, joined in Python |

This project wraps it once:

```python
def with_related(self):
    """One JOIN instead of one query per row — see the N+1 article."""
    return self.select_related('category', 'author')
```

and uses it on every list page. The comments query does the same:

```python
'comments': post.comments.select_related('author').visible_to(request.user),
```

Without it, a post with thirty comments runs thirty extra queries to print thirty usernames.

Symptoms and diagnosis: install **Django Debug Toolbar** and watch the SQL panel. If the query
count grows when the row count grows, you have an N+1. That is the entire diagnostic. Then
pin it with `assertNumQueries`.

## 13.2 Counting things

| Expression | Cost |
| --- | --- |
| `qs.count()` | `SELECT COUNT(*)` — one number |
| `len(qs)` | fetches every row into memory |
| `qs.exists()` | `SELECT 1 ... LIMIT 1` |
| `if qs:` | evaluates the whole queryset |

If you already need the objects, `len()` is free because they are cached. If you only need the
number, `count()`. If you only need to know whether anything is there, `exists()`.

## 13.3 Aggregating in the database

```python
Post.objects.filter(author=request.user).annotate(comment_count=Count('comments'))
```

One query for the posts *and* their comment counts. The loop-and-`.count()` version is one
query per row.

```python
Category.objects.annotate(
    post_count=Count('posts', filter=Q(posts__status=Post.Status.PUBLISHED))
).filter(post_count__gt=0)
```

`annotate` adds a computed column; `aggregate` collapses the whole queryset to a single dict.
Filtering on an annotation produces `HAVING`, and must come in a later `filter()` call than
the `annotate()` that defined it.

## 13.4 Indexes

```python
class Meta:
    indexes = [
        models.Index(fields=['-published_at'], name='post_published_at_idx'),
        models.Index(fields=['status', '-published_at'], name='post_status_pub_idx'),
    ]
```

An index makes reads faster and writes slightly slower, and costs disk. Index what you filter
and sort on, in the order you filter and sort.

The second one is **composite**, and column order matters: an index on `(status, published_at)`
serves a query that filters by status and orders by date — which is precisely
`PostQuerySet.published()`. It would not help a query that filtered only by date.

`unique=True` and `db_index=True` create indexes implicitly, which is why `slug` needs no
explicit one.

## 13.5 Only pay for what you render

```python
posts = list(Post.published.with_related()[:7])
```

Slicing before evaluation puts a `LIMIT` in the SQL. Slicing a list in Python after fetching
seven hundred rows does not.

`only()` and `defer()` trim columns and are a trap: touch a deferred field inside a loop and
you have rebuilt the N+1 you just deleted, one column at a time.

---

# Part 14 — Security

Django gets most of this right by default. The failures are almost always something that was
switched off, or a rule that lives in the template instead of the view.

## 14.1 What you get for free

| Attack | Django's defence | What you must not do |
| --- | --- | --- |
| SQL injection | the ORM parameterises everything | build SQL with f-strings or `.raw()` and string formatting |
| XSS | templates escape every variable | sprinkle the `safe` filter on user input |
| CSRF | token in every POST form | `@csrf_exempt` on an HTML form |
| Clickjacking | `X-Frame-Options: DENY` middleware | remove the middleware |
| Password theft | PBKDF2 with per-user salt | assign to `user.password` directly |
| Session fixation | the session key is cycled on login | roll your own login |

## 14.2 What you must do yourself

**Identity never comes from the form.** `CommentForm` has one field. `PostForm` has no author
field. Both are set from `request.user` after `commit=False`. This is structural: there is no
check to forget, because there is nothing to check.

**Never `fields = '__all__'`.** The day someone adds `is_approved` or `status` to a model, an
`__all__` form starts accepting it from anyone who can POST.

**Check permission in the view, not only in the template.** Every hidden button in this
project has a matching check in the view. The button is courtesy; the view is the security.

**GET must not change state.** Deleting a post takes a confirmation page and then a POST.
Publishing is `@require_POST`. Logging out is a form. Prefetchers, crawlers and link scanners
all follow GETs.

**Choose 403 or 404 deliberately.** 403 confirms the resource exists. For a draft, that is the
leak — so drafts 404.

**Do not leak which half of the login was wrong.** Django's `AuthenticationForm` reports "Please
enter a correct username and password" for both cases, deliberately, so the form cannot be used
to enumerate accounts. There is a test asserting it stays that way.

## 14.3 Before it goes anywhere real

```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']     # never in git

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```

```bash
python manage.py check --deploy
```

That command reads your settings and lists what is unsafe. Run it before every deploy; it
takes a second and it has caught `DEBUG = True` in production more times than anyone admits.

With `DEBUG = True`, an error page shows your settings, your file paths and local variables —
including, on the login view, a POSTed password. That is the whole reason it is not a
"development convenience" but a hard rule.

---

# Part 15 — What changes in production

Not a deployment tutorial. The shape of the change.

**Settings.** One module becomes environment-driven. Read `SECRET_KEY`, `DEBUG`,
`ALLOWED_HOSTS` and the database URL from environment variables. The pattern is a `base.py`
with `dev.py` and `prod.py` importing from it, or a single file reading `os.environ`. Either
is fine; a secret in git is not.

**The database.** SQLite is a real database and a bad fit for a multi-process web server —
one writer at a time, and writes lock the file. Move to PostgreSQL. The ORM code does not
change, which is the point of an ORM.

**Static files.** `runserver` serves them because `DEBUG = True`. In production you run
`python manage.py collectstatic`, which copies every app's static files into `STATIC_ROOT`,
and something else serves that folder — nginx, a CDN, or WhiteNoise inside the app.

**Media files.** `media/` is user-uploaded and must survive a deploy, so it cannot live in the
container's filesystem. Object storage (S3 and friends) via `django-storages`, or a mounted
volume.

**The server.** `runserver` is single-threaded, auto-reloading and explicitly not for
production. Gunicorn or uWSGI runs the WSGI app; nginx sits in front for TLS and static files.

**Migrations.** They run as a deploy step, before the new code starts. On a table with real
size, that is where Part 7's three-step dance stops being an academic exercise.

A minimal checklist:

1. `DEBUG = False`, `ALLOWED_HOSTS` set, `SECRET_KEY` from the environment
2. `python manage.py check --deploy` clean
3. PostgreSQL, with backups you have actually restored once
4. `collectstatic` in the build, media on durable storage
5. HTTPS, with the secure-cookie settings above
6. Migrations as a separate, reviewed deploy step
7. Errors going somewhere a human looks

---

# Part 16 — Reference

## 16.1 Every file

| File | What it holds |
| --- | --- |
| `manage.py` | the command runner |
| `core/settings.py` | apps, database, templates, static and media paths, LOGIN_URL |
| `core/urls.py` | `/admin/`, `/accounts/`, everything else to the blog app, plus dev media |
| `core/wsgi.py`, `core/asgi.py` | deployment entry points |
| `blog/models.py` | Category, Post, Comment, the querysets and managers, the ownership rules |
| `blog/views.py` | ten views |
| `blog/urls.py` | the app URL map, namespaced `blog:` |
| `blog/forms.py` | PostForm, CommentForm, and their validation |
| `blog/admin.py` | list columns, filters, inlines, bulk publish actions |
| `blog/roles.py` | the group-to-permission table |
| `blog/signals.py` | default group on signup, cover cleanup on delete |
| `blog/apps.py` | `ready()` imports the signals |
| `blog/covers.py` | generative cover plates (Pillow) |
| `blog/seed_data.py` | people, sections, articles and comments as plain data |
| `blog/tests.py` | 51 tests |
| `blog/templatetags/blog_extras.py` | `query_string`, `display_name`, `initials`, `recent_posts` |
| `blog/management/commands/seed_blog.py` | builds the demo site |
| `blog/management/commands/sync_roles.py` | applies `roles.py` to the database |
| `blog/migrations/0001` to `0011` | the schema's history |
| `accounts/forms.py` | `RegisterForm` |
| `accounts/views.py` | `register()` |
| `accounts/tests.py` | 13 tests |
| `templates/` | every page and partial |
| `static/css/style.css` | the whole design, one file |

## 16.2 Every URL

| Pattern | Name | View | Access |
| --- | --- | --- | --- |
| `/` | `blog:home` | `index` | public |
| `/posts/` | `blog:post_list` | `post_list` | public |
| `/section/<slug>/` | `blog:category_detail` | `category_detail` | public |
| `/post/<slug>/` | `blog:post_detail` | `post_detail` | public if published |
| `/post/new/` | `blog:post_create` | `post_create` | `blog.add_post` |
| `/post/<slug>/edit/` | `blog:post_edit` | `post_edit` | author or editor |
| `/post/<slug>/delete/` | `blog:post_delete` | `post_delete` | author or editor |
| `/post/<slug>/publish/` | `blog:post_publish` | `post_publish` | author or editor, POST |
| `/comment/<pk>/delete/` | `blog:comment_delete` | `comment_delete` | author or moderator, POST |
| `/comment/<pk>/toggle/` | `blog:comment_toggle` | `comment_toggle` | moderator, POST |
| `/dashboard/` | `blog:dashboard` | `dashboard` | logged in |
| `/about/` | `blog:about` | `about` | public |
| `/accounts/login/` | `login` | Django | public |
| `/accounts/logout/` | `logout` | Django | POST |
| `/accounts/register/` | `register` | `accounts.register` | public |
| `/admin/` | — | Django | staff |

## 16.3 Every model field

**Category** — `name` (unique), `slug` (unique, generated), `description`

**Post** — `title`, `slug` (unique, generated), `content`, `featured_image`, `author` (FK
User, CASCADE), `category` (FK Category, SET_NULL), `status` (draft/published),
`published_at`, `created_at`, `updated_at`

**Comment** — `post` (FK Post, CASCADE), `author` (FK User, CASCADE), `content`,
`is_approved`, `created_at`, `updated_at`

## 16.4 Every permission

| Codename | Source | Held by |
| --- | --- | --- |
| `blog.view_post` | automatic | Readers, Authors, Editors |
| `blog.add_post` | automatic | Authors, Editors |
| `blog.change_post` | automatic | Authors, Editors |
| `blog.delete_post` | automatic | Authors, Editors |
| `blog.can_publish_post` | **custom** | Editors |
| `blog.view_comment` | automatic | all three |
| `blog.add_comment` | automatic | all three |
| `blog.delete_comment` | automatic | all three |
| `blog.change_comment` | automatic | Editors |
| `blog.can_moderate_comment` | **custom** | Editors |
| `blog.add_category` | automatic | Editors |
| `blog.change_category` | automatic | Editors |
| `blog.view_category` | automatic | Editors |

## 16.5 Commands

| Command | Does |
| --- | --- |
| `runserver` | development server on 8000 |
| `makemigrations` | model changes into migration files |
| `migrate` | migration files into the database |
| `sqlmigrate blog 0009` | show the SQL a migration will run |
| `showmigrations` | what is applied |
| `createsuperuser` | an admin account |
| `changepassword <user>` | reset a password |
| `shell` | Python with Django loaded |
| `dbshell` | the database's own client |
| `test` | the suite |
| `check --deploy` | production safety audit |
| `collectstatic` | gather static files for production |
| `sync_roles` | create the three groups from `roles.py` |
| `seed_blog` | build the demo magazine |

## 16.6 Glossary

**App** — a Python package listed in `INSTALLED_APPS`. Django looks in it for models,
migrations, templates and template tags.

**Context** — the dictionary a template renders with.

**Context processor** — a function that adds variables to every template's context. Where
`user`, `perms` and `messages` come from.

**Field lookup** — the double-underscore syntax: `title__icontains`, `category__name`.

**Manager** — the object on `Model.objects` that produces querysets. A model can have several.

**Middleware** — code that wraps every request and response.

**Migration** — a Python file describing a database change.

**MVT** — Model, View, Template. Django's name for MVC, with the words moved around.

**N+1** — one query for a list plus one per row. The most common Django performance bug.

**Namespace** — `app_name` in a urls module, turning `home` into `blog:home`.

**Queryset** — a lazy, chainable description of a database query.

**Slug** — the URL-safe form of a title.

**Signal** — a hook that runs when something happens, such as a model being saved.

**Template tag** — `{% something %}`. Custom ones live in `templatetags/`.

---

# Part 17 — Exercises

In rough order of difficulty. Each is a real feature this project does not have.

**1. A tag system.** Add a `Tag` model and a `ManyToManyField` on `Post`. This is the
relationship the project deliberately lacks, and it will teach you `prefetch_related`, and why
`form.save_m2m()` exists when you use `commit=False`.

**2. Threaded comments.** A `ForeignKey('self', null=True, related_name='replies')`, rendered
as a tree. The hard part is not the model, it is the template — Django templates cannot
recurse, so you will need an inclusion tag that calls itself or a flattened queryset.

**3. Scheduled publishing.** The model already supports it: `PostQuerySet.published()` filters
on `published_at__lte=timezone.now()`, so a future date is already excluded. Add the form
field and prove it with a test.

**4. A third status.** `SUBMITTED`, between draft and published: authors submit, only editors
publish. Change `Status`, adjust `visible_to`, add the transition view, and update the
permission matrix. Notice how little of the codebase you have to touch — that is what the
custom queryset bought you.

**5. Author profile pages.** `/author/<username>/` listing their published work. Then decide
what a visitor sees versus what the author sees on their own page.

**6. Comment editing** with a time limit — editable for five minutes after posting. A new
model method, `is_editable_by`, following the shape of the existing ones.

**7. An RSS feed** using `django.contrib.syndication`. Twenty lines, and it must not leak
drafts. Write that test first.

**8. Full-text search.** Replace the two `icontains` lookups with PostgreSQL's `SearchVector`
and `SearchRank`. This means moving off SQLite, which is a useful exercise in itself.

**9. Convert the views to class-based views.** `ListView`, `DetailView`, `CreateView`,
`UpdateView`, `DeleteView`, and the `UserPassesTestMixin` for the ownership rules. Do it, then
decide honestly which version you would rather debug at midnight.

**10. A REST API** with Django REST Framework. Then work out how the draft rule, the ownership
rule and the moderation rule are expressed in serializers and permission classes — every rule
in Part 6 and Part 7 has to be restated, and finding out how is the lesson.

---

## A closing note

The interesting parts of this project are all in the same place: `blog/models.py`. The status
rule, the visibility rule, the ownership rules, the reusable filters. The views are thin
because the model is not.

That is the pattern worth taking away. A rule that lives in one view will be copied into a
second view, then into a template, and one of those three copies will be wrong. A rule that
lives on the model is asked, not repeated — and when it changes, it changes once.

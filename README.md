# Blog CMS — a Django teaching project

A small magazine built over a class series: posts, sections, signed comments, drafts,
roles and permissions. Server-rendered HTML, SQLite, no build step, no JavaScript framework.

This README gets it running on your machine — **Windows**, **macOS** or **Linux** — and
then explains what is in it. For the long-form walkthrough of *how every piece was built*,
see **`Blog CMS - The Complete Project Guide.docx`** next to this file.

---

## What you end up with

| URL | What it is | Who can see it |
| --- | --- | --- |
| `/` | Front page: lead story plus the latest pieces | everyone |
| `/posts/` | Archive with search, section filter and paging | everyone |
| `/section/<slug>/` | One section, e.g. `/section/django/` | everyone |
| `/post/<slug>/` | An article and its comments | everyone, if published |
| `/post/new/` | Write a piece | needs `blog.add_post` |
| `/post/<slug>/edit/` | Edit a piece | its author, or an editor |
| `/post/<slug>/delete/` | Delete, with a confirmation step | its author, or an editor |
| `/dashboard/` | Your desk: your posts, drafts included | any logged-in user |
| `/about/` | Colophon | everyone |
| `/accounts/login/`, `/accounts/register/` | Auth | everyone |
| `/admin/` | Django admin | staff |

---

## Quick start

If you already know the drill:

```bash
python -m venv venv && source venv/bin/activate   # Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_blog          # 10 articles, 15 accounts, 22 comments, 1 draft
python manage.py createsuperuser    # your own admin login
python manage.py runserver
```

Then open <http://127.0.0.1:8000/>.

The long version follows.

---

## 0. Prerequisites

You need **Python 3.12 or newer** (Django 6.0 does not run on older versions) and **Git**.

**Windows (PowerShell or CMD)**
```powershell
python --version
git --version
```

**macOS / Linux**
```bash
python3 --version
git --version
```

If Python is missing or too old:

- **Windows** — download from [python.org/downloads](https://www.python.org/downloads/).
  During install, **tick "Add python.exe to PATH"** on the first screen. This saves a lot of pain later.
- **macOS** — `brew install python` (install [Homebrew](https://brew.sh/) first), or download from python.org.
- **Linux (Ubuntu/Debian)** — `sudo apt update && sudo apt install python3 python3-venv python3-pip git`

> **`python` vs `python3`:** on Windows it is usually `python`, on macOS/Linux usually `python3`.
> Every command below shows both. Use the one that matches your OS.

---

## 1. Clone the project

```bash
git clone https://github.com/aviralale/django-classes-blog.git
cd django-classes-blog
```

You are now in the folder containing `manage.py`. **Every command from here on runs from this folder.**

---

## 2. Create a virtual environment

A virtual environment ("venv") is a private box of Python packages just for this project, so it
does not collide with anything else on your computer.

**Windows**
```powershell
python -m venv venv
```

**macOS / Linux**
```bash
python3 -m venv venv
```

This creates a `venv/` folder. It is already in `.gitignore`, so it will never be committed.

---

## 3. Activate the virtual environment

The step people forget. You must do it **every time** you open a new terminal.

**Windows — PowerShell**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows — Command Prompt**
```cmd
venv\Scripts\activate.bat
```

**macOS / Linux**
```bash
source venv/bin/activate
```

When it works your prompt gets a `(venv)` prefix:

```
(venv) C:\Users\you\django-classes-blog>
```

> **PowerShell: "running scripts is disabled on this system"?**
> Run this once, then activate again:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

Leave the venv later with `deactivate`.

---

## 4. Install the packages

```bash
pip install -r requirements.txt
```

That is Django plus **Pillow**, which the `ImageField` on `Post` needs and which also
generates the printed cover plates in `blog/covers.py`.

Confirm:

```bash
python -m django --version     # 6.0.7
```

---

## 5. Build the database

`db.sqlite3` is **not** in the repository — everyone builds their own from the migrations:

```bash
python manage.py migrate
```

You will see a list of `OK`s, and a `db.sqlite3` file appears.

---

## 6. Fill it with something to look at

```bash
python manage.py seed_blog
```

This writes:

- the three groups (**Readers**, **Authors**, **Editors**) with their permissions
- 15 accounts, one per byline, all with the password `deskpass123`
- 5 sections and 10 articles — 9 published and **1 deliberate draft**
- 22 comments, each signed by a real account
- a generated two-ink cover plate per article, into `media/blog_images/covers/`

Nothing is invented at random: every article lives in `blog/seed_data.py`, so you can add
one without touching a line of Django.

| Flag | What it does |
| --- | --- |
| *(none)* | add whatever is missing, skip what already exists |
| `--reset` | delete and rewrite the seeded articles |
| `--purge` | **delete every post in the database**, then seed |
| `--skip-users` | do not create demo accounts; attribute everything to the first superuser |

---

## 7. Make your own admin account

```bash
python manage.py createsuperuser
```

It asks for a username, an optional email, and a password.

> **The password is invisible as you type** — no dots, no stars. That is normal. If you pick
> something short, Django warns it is too common; type `y` to accept it anyway. This is a
> practice project.

---

## 8. Run it

```bash
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. Stop the server with **Ctrl + C** (yes, `Ctrl`, not `Cmd`, on macOS too).

---

## The accounts, and why they behave differently

All seeded accounts use the password **`deskpass123`**.

| Account | Group | Can do |
| --- | --- | --- |
| `aviral`, `meghana` | **Editors** | everything an author can, plus publish/unpublish *anyone's* post, see every draft, hide and delete any comment |
| `rohan_dev`, `priya`, `nikhil` | **Authors** | write, edit, publish and delete **their own** posts; comment |
| `sanjay.k`, `devika`, `marcus`, … | **Readers** | comment, and nothing else |

This is worth ten minutes of clicking, because it is the whole authorisation lesson:

1. Log in as **`sanjay.k`** and go to `/post/new/` → **403**. No `blog.add_post` permission.
2. Log in as **`nikhil`** and open the same page → it works. Now try to edit
   `/post/the-n1-query-.../edit/`, which `aviral` wrote → **403**. Right permission, wrong owner.
3. Visit `/post/permissions-are-a-data-model-not-a-decorator/` while logged out → **404**.
   It is a draft. Log in as `aviral` → the page appears with a *Draft* banner.

That last one is deliberate: a draft returns **404**, never 403, because a 403 would confirm
the URL is real and leak the title of something unpublished.

---

## What is in the project

```
blog/
├── manage.py                    ← the command runner
├── requirements.txt
├── db.sqlite3                   ← yours, never committed
│
├── core/                        ← project settings
│   ├── settings.py              ← apps, database, templates, media, LOGIN_URL
│   ├── urls.py                  ← /admin/, /accounts/, everything else → blog/urls.py
│   └── wsgi.py, asgi.py         ← deployment entry points
│
├── blog/                        ← the magazine app
│   ├── models.py                ← Category, Post, Comment + custom queryset/manager
│   ├── views.py                 ← ten views, all function-based
│   ├── urls.py                  ← the app's URL map, namespaced `blog:`
│   ├── forms.py                 ← PostForm, CommentForm and their validation
│   ├── admin.py                 ← list columns, filters, bulk publish actions
│   ├── roles.py                 ← the group → permission table, in version control
│   ├── signals.py               ← default group on signup, cover cleanup on delete
│   ├── apps.py                  ← ready() imports the signals
│   ├── covers.py                ← generates a two-ink cover plate per slug (Pillow)
│   ├── seed_data.py             ← the articles, people and sections as plain data
│   ├── tests.py                 ← 51 tests of this project's rules
│   ├── templatetags/
│   │   └── blog_extras.py       ← query_string, display_name, initials, recent_posts
│   ├── management/commands/
│   │   ├── seed_blog.py         ← builds the demo site
│   │   └── sync_roles.py        ← applies roles.py to the database
│   └── migrations/              ← the database's version history
│
├── accounts/                    ← registration only; login/logout come from Django
│   ├── forms.py                 ← RegisterForm (UserCreationForm + required email)
│   ├── views.py                 ← register(), which logs you in afterwards
│   └── tests.py
│
├── templates/
│   ├── base.html                ← masthead, nav, messages, footer
│   ├── 403.html, 404.html       ← used when DEBUG = False
│   ├── registration/            ← login.html, register.html
│   └── blog/
│       ├── home.html, post_list.html, category_detail.html
│       ├── post_detail.html, post_form.html, post_confirm_delete.html
│       ├── dashboard.html, about.html
│       └── partials/            ← _card, _comment, _field, _pagination, _recent
│
├── static/css/style.css         ← the whole design, one file, no framework
└── media/                       ← uploaded and generated images
```

### How a request flows

```
Browser asks for /post/caching-is-a-bet-about-the-future/
        ↓
core/urls.py      → not /admin/ or /accounts/, so hand it to blog/urls.py
        ↓
blog/urls.py      → matches 'post/<slug:slug>/', captures slug="caching-is-..."
        ↓
blog/views.py     → post_detail() asks for it from Post.objects.visible_to(request.user)
                    · published? everyone gets it
                    · draft?     only the author and the editors; everyone else 404
        ↓
templates/blog/post_detail.html  → renders the article, the comments and the form
        ↓
Browser shows the page
```

---

## The features, and where to read them

| Feature | Start here |
| --- | --- |
| Draft vs published | `Post.Status`, `Post.save()`, `PostQuerySet.published()` |
| Only the author sees their draft | `PostQuerySet.visible_to()`, `Post.is_visible_to()` |
| Custom permissions | `Post.Meta.permissions`, `Comment.Meta.permissions` |
| Groups and who gets what | `blog/roles.py`, then `python manage.py sync_roles` |
| Ownership vs permission | `Post.is_editable_by()` — a permission gates the verb, ownership gates the row |
| Login required to comment | `views.post_detail`, and `CommentForm` having no name field |
| Comment moderation | `Comment.is_approved`, `views.comment_toggle` |
| Flash messages | `django.contrib.messages`, rendered in `base.html` |
| Pagination that keeps your search | `views.paginate` + the `query_string` template tag |
| Search and filtering | `PostQuerySet.search()` with `Q` objects |
| Avoiding N+1 queries | `PostQuerySet.with_related()`, and `QueryCountTests` which fails if it is removed |
| Signals | `blog/signals.py`, wired up in `blog/apps.py` |

---

## Commands

All of these need the venv active.

| Command | What it does |
| --- | --- |
| `python manage.py runserver` | Start the dev server on port 8000 |
| `python manage.py runserver 8080` | Start it on a different port |
| `python manage.py makemigrations` | Turn model changes into migration files |
| `python manage.py migrate` | Apply migrations to the database |
| `python manage.py createsuperuser` | Create an admin login |
| `python manage.py sync_roles` | Create/refresh the three groups from `roles.py` |
| `python manage.py seed_blog` | Build the demo magazine |
| `python manage.py test` | Run the test suite |
| `python manage.py shell` | A Python shell with Django loaded |

Poking around in the shell:

```python
>>> from blog.models import Post
>>> Post.objects.count()          # everything, drafts included
>>> Post.published.count()        # only what the public can see
>>> Post.objects.drafts()
>>> Post.published.with_related().search('cache')
>>> p = Post.published.first()
>>> p.reading_time, p.excerpt
```

---

## Tests

```bash
python manage.py test              # everything
python manage.py test blog         # just the blog app
python manage.py test blog.tests.DraftVisibilityTests -v 2
```

64 tests. None of them assert that Django works — they assert the rules *this* project
invented: drafts stay private, comments need an account, authors cannot edit each other's
work, publishing stamps the date once and never moves it.

---

## Troubleshooting

**`python: command not found` / `'python' is not recognized`**
Try `python3`. On Windows this usually means Python is not on PATH — reinstall and tick
**"Add python.exe to PATH"**.

**`No module named django`**
The venv is not active (no `(venv)` in your prompt), or step 4 was skipped.

**PowerShell: `Activate.ps1 cannot be loaded because running scripts is disabled`**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**`Error: That port is already in use.`**
Another server is still running. Close that terminal, or `python manage.py runserver 8001`.

**`no such table: blog_post`**
You skipped `python manage.py migrate`.

**`You have unapplied migrations`**
Run `python manage.py migrate`.

**Changed a model and nothing happened**
Model edits need two commands:
```bash
python manage.py makemigrations
python manage.py migrate
```

**A new post does not appear on the front page**
It is a draft. Publish it from `/dashboard/`, from the post page, or in the admin.

**403 when trying to write**
Your account has no `blog.add_post` permission. Run `python manage.py sync_roles`, then put
yourself in **Authors** in the admin under *Users → your user → Groups*.

**Everyone can suddenly do everything**
You are logged in as a superuser. Superusers bypass every permission check by design —
test authorisation with a normal account.

**`{% load blog_extras %}` raises `'blog_extras' is not a registered tag library`**
Restart the dev server. The tag registry is built at startup and does not autoreload.

**Images 404 in development**
`media/` is served by the `static()` line at the bottom of `core/urls.py`, which only works
when `DEBUG = True`. In production a real web server serves that folder.

---

## Notes for students

- `db.sqlite3`, `venv/` and `media/` are intentionally **not** in the repo. Everyone builds
  their own from step 5.
- The `SECRET_KEY` in `core/settings.py` and `DEBUG = True` are fine for learning and must
  never ship to a real server.
- Broke something? `git status` shows what changed, and `git checkout -- <file>` throws away
  your edits to that file.

### Things to build next

1. **Tags**, as a `ManyToManyField` — the relationship this project deliberately does not have yet.
2. **Reply-to-comment**, a self-referencing `ForeignKey('self')`, rendered as a tree.
3. **Scheduled publishing.** The model already supports it: `published_at` in the future is
   excluded by `PostQuerySet.published()`. All that is missing is a form field and a cron job.
4. **Drafts that need editor approval** — a third status, `SUBMITTED`, between draft and published.
5. **Convert the views to class-based views** and see what you gain and what you lose.

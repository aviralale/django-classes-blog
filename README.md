# django-classes-blog

A small Django blog built during class — posts, dynamic URLs, templates, and the admin panel.

This README is a step-by-step tutorial. Follow it top to bottom and you'll have the project
running on your own machine, whether you're on **Windows**, **macOS**, or **Linux**.

---

## What you'll end up with

| URL | What it shows |
| --- | --- |
| `http://127.0.0.1:8000/` | Home page listing every blog post |
| `http://127.0.0.1:8000/post/<slug>/` | A single post's detail page |
| `http://127.0.0.1:8000/about/` | A plain "about" page |
| `http://127.0.0.1:8000/admin/` | Django admin, where you create posts |

---

## 0. Prerequisites

You need **Python 3.12 or newer** (Django 6.0 does not run on older versions) and **Git**.

Check what you have:

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
  During install, **tick "Add python.exe to PATH"** on the first screen. This saves you a lot of pain later.
- **macOS** — `brew install python` (install [Homebrew](https://brew.sh/) first), or download from python.org.
- **Linux (Ubuntu/Debian)** — `sudo apt update && sudo apt install python3 python3-venv python3-pip git`

> **Note on the `python` vs `python3` command:** on Windows it's usually `python`,
> on macOS/Linux it's usually `python3`. Every command below shows both. Use the one that matches your OS.

---

## 1. Clone the project

```bash
git clone https://github.com/aviralale/django-classes-blog.git
cd django-classes-blog
```

You're now inside the project folder — the one containing `manage.py`. **Every command from here on
is run from this folder.**

---

## 2. Create a virtual environment

A virtual environment ("venv") is a private box of Python packages just for this project, so it
doesn't collide with anything else on your computer.

**Windows**
```powershell
python -m venv venv
```

**macOS / Linux**
```bash
python3 -m venv venv
```

This creates a `venv/` folder. It's already in `.gitignore`, so it will never be committed.

---

## 3. Activate the virtual environment

This is the step people forget. You must do it **every time** you open a new terminal to work on the project.

**Windows — PowerShell**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows — Command Prompt (CMD)**
```cmd
venv\Scripts\activate.bat
```

**macOS / Linux**
```bash
source venv/bin/activate
```

When it works, your prompt gets a `(venv)` prefix:

```
(venv) C:\Users\you\django-classes-blog>
```

> **PowerShell error: "running scripts is disabled on this system"?**
> Run this once, then try activating again:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

To leave the venv later, type `deactivate`.

---

## 4. Install Django

With `(venv)` showing in your prompt:

```bash
pip install -r requirements.txt
```

Confirm it landed:

```bash
python -m django --version
```

You should see `6.0.5`.

---

## 5. Set up the database

The database file (`db.sqlite3`) is **not** in the repository — everyone builds their own. These
commands create it from the migrations in `blog/migrations/`:

```bash
python manage.py migrate
```

You'll see a list of `OK`s. A `db.sqlite3` file now exists in the project folder.

---

## 6. Create an admin account

You need a login to reach the admin panel and add posts:

```bash
python manage.py createsuperuser
```

It asks for a username, an (optional) email, and a password.

> **The password is invisible as you type** — no dots, no stars. That's normal, keep typing and press Enter.
> If you pick something short like `admin123`, Django will warn it's too common; type `y` to accept it anyway.
> This is a practice project, so a simple password is fine.

---

## 7. Run the server

```bash
python manage.py runserver
```

Output:

```
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

Open **http://127.0.0.1:8000/** in your browser. You'll see "Welcome to my blog" with no posts yet —
that's expected, your database is empty. Let's fix that.

> Stop the server any time with **Ctrl + C** (yes, `Ctrl`, not `Cmd`, on macOS too).

---

## 8. Add your first post

1. Leave the server running and go to **http://127.0.0.1:8000/admin/**
2. Log in with the superuser you just created.
3. Click **Posts → Add Post**.
4. Fill in **Title**, **Content**, **Author**, and **Category**. **Leave Slug empty.**
5. Click **Save**.

Now refresh **http://127.0.0.1:8000/** — your post is on the home page.

### About that slug

The slug is the URL-friendly version of your title, generated automatically in `blog/models.py`
when you save: it lowercases the title and swaps spaces for dashes.

> `My Country Nepal` → `my-country-nepal` → `http://127.0.0.1:8000/post/my-country-nepal/`

If two posts end up with the same slug, Django appends a number (`my-country-nepal-1`).

**The home page doesn't link to the detail pages yet** — that's a feature still to be built. For now,
type the post URL in the address bar yourself, or copy the slug from the post's page in the admin.

---

## Coming back to the project later

Once set up, your daily loop is only two commands:

```bash
# 1. activate the venv (pick your platform's line)
.\venv\Scripts\Activate.ps1     # Windows PowerShell
venv\Scripts\activate.bat       # Windows CMD
source venv/bin/activate        # macOS / Linux

# 2. run the server
python manage.py runserver
```

---

## Project structure

```
django-classes-blog/
├── manage.py               ← the command runner (runserver, migrate, ...)
├── requirements.txt        ← the packages this project needs
├── db.sqlite3              ← your local database (created by migrate, never committed)
│
├── core/                   ← project-level settings
│   ├── settings.py         ← installed apps, database, template folder
│   ├── urls.py             ← top-level routes: /admin/ and everything else → blog/urls.py
│   ├── wsgi.py / asgi.py   ← deployment entry points (ignore for now)
│
├── blog/                   ← the blog app
│   ├── models.py           ← the Post model + automatic slug generation
│   ├── views.py            ← index, post_detail, about
│   ├── urls.py             ← /, /post/<slug>/, /about/
│   ├── admin.py            ← registers Post with the admin panel
│   └── migrations/         ← the database's version history
│
└── templates/blog/
    ├── home.html           ← the post list
    └── post_detail.html    ← one post
```

### How a request flows

```
Browser asks for /post/my-first-post/
        ↓
core/urls.py       → not /admin/, so hand it to blog/urls.py
        ↓
blog/urls.py       → matches 'post/<slug:slug>/', captures slug="my-first-post"
        ↓
blog/views.py      → post_detail() fetches that Post (404 if it doesn't exist)
        ↓
templates/blog/post_detail.html  → renders the HTML
        ↓
Browser shows the page
```

---

## Useful commands

All of these need the venv active.

| Command | What it does |
| --- | --- |
| `python manage.py runserver` | Start the dev server on port 8000 |
| `python manage.py runserver 8080` | Start it on a different port |
| `python manage.py makemigrations` | Turn model changes into migration files |
| `python manage.py migrate` | Apply migrations to the database |
| `python manage.py createsuperuser` | Create an admin login |
| `python manage.py shell` | Open a Python shell with Django loaded |
| `pip install -r requirements.txt` | Install the project's packages |

Playing with posts in the shell:

```python
>>> from blog.models import Post
>>> Post.objects.all()
>>> Post.objects.count()
>>> Post.objects.create(title="Hello World", content="My first post", author="You", category="General")
>>> exit()
```

---

## Troubleshooting

**`python: command not found` / `'python' is not recognized`**
Try `python3` instead. On Windows, this usually means Python wasn't added to PATH — reinstall it and
tick **"Add python.exe to PATH"**.

**`No module named django`**
The venv isn't active (no `(venv)` in your prompt), or step 4 was skipped. Activate it, then
`pip install -r requirements.txt`.

**PowerShell: `Activate.ps1 cannot be loaded because running scripts is disabled`**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**`Error: That port is already in use.`**
Another server is still running. Close that terminal, or use a different port:
```bash
python manage.py runserver 8001
```

**`no such table: blog_post`**
You skipped `python manage.py migrate`. Run it.

**Home page loads but shows no posts**
The database is empty. Add a post through the admin (step 8).

**404 on a post URL**
The slug is wrong. Check the exact slug in the admin — it's the lowercased title with dashes instead
of spaces, e.g. `My First Post` → `/post/my-first-post/`.

**`You have unapplied migrations` warning on startup**
Run `python manage.py migrate`.

**Changed a model and nothing happened**
Model edits need two commands:
```bash
python manage.py makemigrations
python manage.py migrate
```

---

## Notes for students

- `db.sqlite3` and `venv/` are intentionally **not** in the repo. Your database and packages are yours;
  everyone builds them from step 5.
- The `SECRET_KEY` in `core/settings.py` and `DEBUG = True` are fine for learning, but must never ship
  to a real server.
- Broke something badly? `git status` shows what you changed, and `git checkout -- <file>` throws away
  your edits to that file.

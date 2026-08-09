"""Who is allowed to do what, in one file.

Django has two ways to answer "can this user do X":

  * **Permissions** — one flag per action per model. Django creates four for
    every model automatically (`add_`, `change_`, `delete_`, `view_`), and you
    can declare your own in `Meta.permissions`. This project adds two:
    `can_publish_post` and `can_moderate_comment`.

  * **Groups** — named bundles of permissions. You attach the *group* to the
    user, so promoting someone is one click instead of twelve checkboxes.

Never hand permissions to individual users. Put them in a group, put the user
in the group, and keep the group list here in version control where a code
review can see it. `python manage.py sync_roles` applies this file.
"""

# Comment permissions everyone signed-in needs.
_COMMENTING = [
    'blog.view_post',
    'blog.view_comment',
    'blog.add_comment',
    'blog.delete_comment',
]

# Writing your own pieces.
_WRITING = [
    'blog.add_post',
    'blog.change_post',
    'blog.delete_post',
]

ROLES = {
    # Signed up, can talk, cannot publish. Hitting /post/new/ gives them a 403.
    'Readers': _COMMENTING,

    # The default for a new account: can write, edit and publish *their own*
    # posts. The "their own" half is not a permission — it is the ownership
    # check in Post.is_editable_by(). Permissions gate the action, ownership
    # gates the row.
    'Authors': _COMMENTING + _WRITING,

    # Runs the magazine. The two custom permissions are what separate an
    # editor from an author: they apply to *anyone's* post or comment.
    'Editors': _COMMENTING + _WRITING + [
        'blog.can_publish_post',
        'blog.can_moderate_comment',
        'blog.change_comment',
        'blog.add_category',
        'blog.change_category',
        'blog.view_category',
    ],
}

# Every new account lands here — see blog/signals.py.
DEFAULT_ROLE = 'Authors'

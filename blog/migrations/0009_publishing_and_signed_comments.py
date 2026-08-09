"""Step 1 of 3: add the new columns, all of them loose.

Nothing here can fail on an existing database. Every new column is either
nullable or has a default, and no old column is removed yet. The tightening
happens in 0011, after 0010 has filled the new columns in.

That order — add loose, backfill, tighten — is the only safe way to change a
table that already has rows in it, and it is exactly what you would do on a
production database with a rolling deploy.
"""

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0008_alter_post_author_alter_post_content'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # --- Category gets a URL-safe name and a blurb ---------------------
        migrations.AddField(
            model_name='category',
            name='slug',
            field=models.SlugField(blank=True, default='', max_length=64),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='category',
            name='description',
            field=models.CharField(blank=True, default='', max_length=200),
            preserve_default=False,
        ),

        # --- Post learns about drafts -------------------------------------
        migrations.AddField(
            model_name='post',
            name='status',
            field=models.CharField(
                choices=[('draft', 'Draft'), ('published', 'Published')],
                default='draft',
                max_length=10,
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
            field=models.DateTimeField(
                auto_now=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='post',
            name='title',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='post',
            name='content',
            # Was TextField(max_length=100), which silently capped every
            # article at 100 characters in the form layer.
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='post',
            name='slug',
            field=models.SlugField(blank=True, max_length=220, unique=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='category',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='posts',
                to='blog.category',
            ),
        ),

        # --- Comment gets a real author -----------------------------------
        migrations.AddField(
            model_name='comment',
            name='author',
            # Nullable for now: 0010 fills it, 0011 makes it required.
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='comments',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='comment',
            name='is_approved',
            field=models.BooleanField(
                default=True,
                help_text='Untick to hide the comment from everyone except its author.',
            ),
        ),
        migrations.AddField(
            model_name='comment',
            name='updated_at',
            field=models.DateTimeField(
                auto_now=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
    ]

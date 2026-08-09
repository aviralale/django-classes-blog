"""Step 3 of 3: now that the data is clean, enforce it.

Every operation in here would have crashed if it had run before 0010:
a unique index on a column full of empty strings, a NOT NULL on a column
full of nulls. Order is the whole trick.

The old `Comment.name` column is dropped last. Once this migration runs the
free-text name is gone for good, which is why 0010 turned it into a real
account first.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0010_backfill_publishing_data'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=54, unique=True),
        ),
        migrations.AlterField(
            model_name='category',
            name='slug',
            field=models.SlugField(blank=True, max_length=64, unique=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='author',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='posts',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='comment',
            name='author',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='comments',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RemoveField(
            model_name='comment',
            name='name',
        ),

        # --- Meta: ordering, indexes and the custom permissions -----------
        migrations.AlterModelOptions(
            name='post',
            options={
                'ordering': ['-published_at', '-created_at'],
                'permissions': [
                    ('can_publish_post', 'Can publish or unpublish any post')
                ],
            },
        ),
        migrations.AlterModelOptions(
            name='comment',
            options={
                'ordering': ['created_at'],
                'permissions': [
                    ('can_moderate_comment', "Can hide or delete anyone's comment")
                ],
            },
        ),
        migrations.AddIndex(
            model_name='post',
            index=models.Index(
                fields=['-published_at'], name='post_published_at_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='post',
            index=models.Index(
                fields=['status', '-published_at'], name='post_status_pub_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(
                fields=['post', 'created_at'], name='comment_post_created_idx'
            ),
        ),
    ]

from django.db import models
from django.urls import reverse
from django.utils.text import Truncator, slugify

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=54)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    featured_image = models.ImageField(upload_to='blog_images/', default='blog_images/default.png')
    #https://blog.ctrlbits.com/post/software-development-life-cycle-for-2026-developers
    slug = models.CharField(max_length=100, unique=True, blank=True)
    author = models.CharField(max_length=100)
    # category = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            # base_slug = self.title.lower().replace(' ','-')
            base_slug = slugify(self.title)
            #My Country Nepal --> my-country-nepal
            slug = base_slug
            counter = 1
            while Post.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.slug})

    @property
    def excerpt(self):
        """First slice of the article, used on the cards."""
        return Truncator(self.content).chars(190)

    @property
    def reading_time(self):
        """Minutes, at a lazy 200 words per minute."""
        words = len(self.content.split())
        return max(1, round(words / 200))

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    name = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.name} on {self.post.title}"

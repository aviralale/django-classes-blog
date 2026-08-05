from django.db import models
from django.utils.text import slugify

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=54)

    def __str__(self):
        return self.name

class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    #https://blog.ctrlbits.com/post/software-development-life-cycle-for-2026-developers
    slug = models.CharField(max_length=100, unique=True, blank=True)
    author = models.CharField(max_length=100)
    # category = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

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


    def __str__(self):
        return self.title
    
    
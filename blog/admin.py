from django.contrib import admin
from .models import Post, Category, Comment

# Register your models here.
admin.site.site_header = "Blog CMS Administration"
admin.site.site_title = "Blog CMS Admin Portal"
admin.site.index_title = "Welcome to the Blog CMS Admin Portal"


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'created_at')
    list_filter = ('category', 'author')
    search_fields = ('title', 'content')
    date_hierarchy = 'created_at'
    inlines = [CommentInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('name', 'post', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'content')

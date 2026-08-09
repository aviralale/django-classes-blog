"""The admin.

You get a working CRUD backend for free the moment you call `register()`.
Everything below is decoration: which columns to show, which filters to offer,
which bulk actions to allow, and — the part people forget — which rows a given
staff member is even allowed to see.
"""

from django.contrib import admin, messages
from django.db.models import Count
from django.utils import timezone

from .models import Category, Comment, Post

admin.site.site_header = 'Blog CMS Administration'
admin.site.site_title = 'Blog CMS Admin Portal'
admin.site.index_title = 'Welcome to the Blog CMS Admin Portal'


class CommentInline(admin.TabularInline):
    """Comments edited on the post's own page instead of a separate screen."""

    model = Comment
    extra = 0
    fields = ('author', 'content', 'is_approved', 'created_at')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('author',)


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

    def get_queryset(self, request):
        """One query for the list page, plus a comment count.

        Without `select_related` the changelist runs two extra queries per row
        to render the category and author columns.
        """
        return (
            super()
            .get_queryset(request)
            .select_related('category', 'author')
            .annotate(_comments=Count('comments'))
        )

    @admin.display(description='Comments', ordering='_comments')
    def comment_count(self, obj):
        return obj._comments

    @admin.display(description='Status', ordering='status')
    def status_badge(self, obj):
        return '● Published' if obj.is_published else '○ Draft'

    def save_model(self, request, obj, form, change):
        """A post created in the admin belongs to whoever created it."""
        if not change and not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    # --- bulk actions ---------------------------------------------------

    @admin.action(description='Publish selected posts', permissions=['publish'])
    def publish_selected(self, request, queryset):
        updated = queryset.filter(status=Post.Status.DRAFT).update(
            status=Post.Status.PUBLISHED, published_at=timezone.now()
        )
        self.message_user(request, f'{updated} post(s) published.', messages.SUCCESS)

    @admin.action(description='Move selected posts back to draft', permissions=['publish'])
    def unpublish_selected(self, request, queryset):
        updated = queryset.filter(status=Post.Status.PUBLISHED).update(
            status=Post.Status.DRAFT, published_at=None
        )
        self.message_user(request, f'{updated} post(s) moved to draft.', messages.WARNING)

    def has_publish_permission(self, request):
        """Backs `permissions=['publish']` above — Django looks for a method
        named `has_<name>_permission` on the ModelAdmin."""
        return request.user.has_perm('blog.can_publish_post')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'post_count')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_posts=Count('posts'))

    @admin.display(description='Posts', ordering='_posts')
    def post_count(self, obj):
        return obj._posts


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'short_content', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('content', 'author__username')
    autocomplete_fields = ('post', 'author')
    list_editable = ('is_approved',)
    actions = ['approve_selected', 'hide_selected']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('post', 'author')

    @admin.display(description='Comment')
    def short_content(self, obj):
        return obj.content[:60] + ('…' if len(obj.content) > 60 else '')

    @admin.action(description='Approve selected comments', permissions=['moderate'])
    def approve_selected(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} comment(s) approved.', messages.SUCCESS)

    @admin.action(description='Hide selected comments', permissions=['moderate'])
    def hide_selected(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} comment(s) hidden.', messages.WARNING)

    def has_moderate_permission(self, request):
        return request.user.has_perm('blog.can_moderate_comment')

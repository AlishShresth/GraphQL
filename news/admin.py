from django.contrib import admin
from .models import Tag, Article, Comment, Like, Bookmark


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "category",
        "status",
        "is_featured",
        "views_count",
        "published_at",
    )
    list_filter = ("status", "is_featured", "category", "created_at", "published_at")
    search_fields = ("title", "summary" "content")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
    date_hierarchy = "published_at"
    ordering = ("-published_at", "-created_at")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("user", "article", "is_approved", "created_at")
    list_filter = ("is_approved", "created_at")
    search_fields = ("user__username", "article__title", "content")


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("user", "article", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "article__title")


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ("user", "article", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "article__title")

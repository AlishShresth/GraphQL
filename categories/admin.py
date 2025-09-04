from django.contrib import admin
from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent", "created_at")
    list_filter = ("parent", "created_at")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}

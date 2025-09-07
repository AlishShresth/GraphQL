from django.db import models
from django.db.models import Q
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank, SearchVectorField
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse

from categories.models import Category


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.name.lower().replace(" ", "-")
        super().save(*args, **kwargs)


class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = ("draft", _("Draft"))
        PUBLISHED = ("published", _("Published"))

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True, null=True)
    summary = models.TextField(max_length=500, help_text="Brief summary of the article")
    content = models.TextField()
    featured_image = models.ImageField(
        upload_to="article_images/", blank=True, null=True
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="articles"
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="articles"
    )
    tags = models.ManyToManyField(Tag, blank=True, null=True, related_name="articles")
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.DRAFT
    )
    is_featured = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    search_vector = SearchVectorField(null=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        verbose_name = _("Article")
        verbose_name_plural = _("Articles")
        indexes = [
            models.Index(fields=["search_vector"], name="article_search_idx"),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        if self.status == "published" and not self.published_at:
            from django.utils import timezone

            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("article_detail", kwargs={"slug": self.slug})

    @property
    def is_published(self):
        return self.status == "published"

    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=["views_count"])

    @classmethod
    def search(cls, query):
        """Perform full-text search on articles.
        Returns articles ordered by relevance.
        """
        if not query:
            return cls.objects.none()

        search_query = SearchQuery(query)
        search_vector = (
            SearchVector("title", weight="A")
            + SearchVector("summary", weight="B")
            + SearchVector("content", weight="C")
        )

        return (
            cls.objects.annotate(
                search=search_vector, rank=SearchRank(search_vector, search_query)
            )
            .filter(Q(search=search_query) & Q(status="published"))
            .order_by("-rank", "-published_at")
        )


class Comment(models.Model):
    article = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name="comments"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments"
    )
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    content = models.TextField()
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = _("Comment")
        verbose_name_plural = _("Comments")

    @property
    def children(self):
        return Comment.objects.filter(parent=self)


class Like(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="liked_articles",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("article", "user")

    def __str__(self):
        return f"{self.user.username} likes {self.article.title}"


class Bookmark(models.Model):
    article = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name="bookmarks"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookmarked_articles",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("article", "user")

    def __str__(self):
        return f"{self.user.username} bookmarked {self.article.title}"

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    class Role(models.TextChoices):
        READER = ("reader", _("Reader"))
        JOURNALIST = ("journalist", _("Journalist"))
        EDITOR = ("editor", _("Editor"))

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.READER)
    bio = models.TextField(blank=True)
    profile_image = models.ImageField(
        upload_to="profile_images/", blank=True, null=True
    )
    website = models.URLField(blank=True, null=True)
    twitter = models.CharField(max_length=15, blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)
    instagram = models.CharField(max_length=30, blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

    @property
    def is_journalist(self):
        return self.role == "journalist"

    @property
    def is_editor(self):
        return self.role == "editor"

    @property
    def is_reader(self):
        return self.role == "reader"

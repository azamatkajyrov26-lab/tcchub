from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Administrator"
        MANAGER = "manager", "Manager"
        COURSE_CREATOR = "course_creator", "Course Creator"
        TEACHER = "teacher", "Teacher"
        ASSISTANT = "assistant", "Teaching Assistant"
        STUDENT = "student", "Student"
        GUEST = "guest", "Guest"

    class Language(models.TextChoices):
        RU = "ru", "Russian"
        KK = "kk", "Kazakh"
        EN = "en", "English"

    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to="avatars/%Y/%m/", blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=50, default="Asia/Aqtau")
    language = models.CharField(max_length=2, choices=Language.choices, default=Language.RU)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    phone = models.CharField(max_length=20, blank=True)
    last_ip = models.GenericIPAddressField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        ordering = ["-date_joined"]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.get_full_name() or self.email


class UserProfile(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="profile"
    )
    bio = models.TextField(blank=True)
    social_links = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Profile: {self.user}"

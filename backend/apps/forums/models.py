from django.conf import settings
from django.db import models


class Forum(models.Model):
    class ForumType(models.TextChoices):
        GENERAL = "general", "General"
        NEWS = "news", "News"
        QA = "qa", "Q&A"
        BLOG = "blog", "Blog"

    activity = models.OneToOneField(
        "content.Activity", on_delete=models.CASCADE, related_name="forum"
    )
    forum_type = models.CharField(max_length=10, choices=ForumType.choices, default=ForumType.GENERAL)
    is_anonymous = models.BooleanField(default=False)

    def __str__(self):
        return f"Forum: {self.activity.title}"


class Discussion(models.Model):
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE, related_name="discussions")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="discussions"
    )
    title = models.CharField(max_length=255)
    pinned = models.BooleanField(default=False)
    locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-pinned", "-created_at"]

    def __str__(self):
        return self.title


class Post(models.Model):
    discussion = models.ForeignKey(Discussion, on_delete=models.CASCADE, related_name="posts")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="forum_posts"
    )
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Post by {self.user} in {self.discussion.title}"

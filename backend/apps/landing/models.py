from django.db import models


class HeroSection(models.Model):
    title = models.CharField(max_length=255)
    subtitle = models.TextField(blank=True)
    background_image = models.ImageField(upload_to="landing/hero/", blank=True)
    cta_text = models.CharField(max_length=100, blank=True)
    cta_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Hero sections"

    def __str__(self):
        return self.title


class Metric(models.Model):
    label = models.CharField(max_length=100)
    value = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.label}: {self.value}"


class Partner(models.Model):
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to="landing/partners/")
    url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


class Testimonial(models.Model):
    author_name = models.CharField(max_length=255)
    author_role = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    avatar = models.ImageField(upload_to="landing/testimonials/", blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.author_name} - {self.author_role}"


class Advantage(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=100, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class ContactInfo(models.Model):
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    whatsapp = models.CharField(max_length=50, blank=True)
    linkedin = models.URLField(blank=True)
    instagram = models.URLField(blank=True)

    class Meta:
        verbose_name_plural = "Contact info"

    def __str__(self):
        return self.email or "Contact Info"

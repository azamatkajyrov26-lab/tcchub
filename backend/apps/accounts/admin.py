from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import CustomUser, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    list_display = ["email", "username", "first_name", "last_name", "role", "is_active", "date_joined"]
    list_filter = ["role", "is_active", "language"]
    list_filter_submit = True
    search_fields = ["email", "username", "first_name", "last_name"]
    ordering = ["-date_joined"]
    inlines = [UserProfileInline]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Дополнительно", {"fields": ("avatar", "city", "country", "timezone", "language", "role", "phone", "last_ip")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Дополнительно", {"fields": ("email", "role")}),
    )

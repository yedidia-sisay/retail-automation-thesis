from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User


class CustomUserAdmin(UserAdmin):
    """
    Extends Django's built-in UserAdmin to ensure the required fields
    (username, first_name, last_name, email, is_staff, is_active, groups)
    are visible and editable in the Django Admin interface.
    """

    # Fields shown in the user list view
    list_display = (
        "username",
        "first_name",
        "last_name",
        "email",
        "is_staff",
        "is_active",
    )

    # Ensure groups is included in the editable fieldsets.
    # UserAdmin already includes groups in its default fieldsets under
    # "Permissions", so we override to make the layout explicit and
    # guarantee all required fields are present.
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Personal info",
            {"fields": ("first_name", "last_name", "email")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )


# Unregister the default User admin and register the custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

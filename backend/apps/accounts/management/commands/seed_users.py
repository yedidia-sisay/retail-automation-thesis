from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed required groups and a default cashier user for development."

    def handle(self, *args, **options):
        # --- Groups ---
        admin_group, admin_created = Group.objects.get_or_create(name="Admin")
        if admin_created:
            self.stdout.write(self.style.SUCCESS("Created group: Admin"))
        else:
            self.stdout.write("Skipped group (already exists): Admin")

        cashier_group, cashier_created = Group.objects.get_or_create(name="Cashier")
        if cashier_created:
            self.stdout.write(self.style.SUCCESS("Created group: Cashier"))
        else:
            self.stdout.write("Skipped group (already exists): Cashier")

        # --- Default cashier user ---
        # WARNING: The default password "123" MUST be changed before deploying to production.
        user, user_created = User.objects.get_or_create(
            username="adamreta",
            defaults={
                "first_name": "Adam",
                "last_name": "Reta",
                "is_staff": False,
                "is_superuser": False,
                "is_active": True,
            },
        )

        if user_created:
            user.set_password("123")
            user.save()
            user.groups.add(cashier_group)
            self.stdout.write(self.style.SUCCESS("Created user: adamreta"))
        else:
            self.stdout.write("Skipped user (already exists): adamreta")

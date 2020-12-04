from django.core.management.base import BaseCommand
from website.models import User


class Command(BaseCommand):
    help = "Recompute all user stats"

    def handle(self, *args, **options):
        User.objects.recompute_ranks()
        self.stdout.write(self.style.SUCCESS("Successfully recomputed all stats"))

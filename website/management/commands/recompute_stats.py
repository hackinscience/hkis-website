from django.core.management.base import BaseCommand, CommandError
from website.models import UserStats, Exercise


class Command(BaseCommand):
    help = "Recompute all user stats"

    def handle(self, *args, **options):
        UserStats.objects.recompute()
        self.stdout.write(self.style.SUCCESS("Successfully recomputed all stats"))

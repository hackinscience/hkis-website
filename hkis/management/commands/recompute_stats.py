from django.core.management.base import BaseCommand
from hkis.models import User, Team


class Command(BaseCommand):
    help = "Recompute all user stats"

    def handle(self, *args, **options):
        Team.objects.recompute_ranks()
        User.objects.recompute_ranks()
        self.stdout.write(self.style.SUCCESS("Successfully recomputed all stats"))

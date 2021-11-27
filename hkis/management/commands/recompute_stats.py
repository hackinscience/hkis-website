from django.core.management.base import BaseCommand
from hkis.models import Team, UserInfo


class Command(BaseCommand):
    help = "Recompute all user stats"

    def handle(self, *args, **options):
        Team.objects.recompute_ranks()
        UserInfo.objects.recompute_ranks()
        self.stdout.write(self.style.SUCCESS("Successfully recomputed all stats"))

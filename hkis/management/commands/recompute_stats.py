from django.core.management.base import BaseCommand
from hkis.models import Team, UserInfo, Exercise


class Command(BaseCommand):
    help = "Recompute all user stats"

    def handle(self, *args, **options):
        self.stdout.write("Recomputing exercises solved_by...")
        Exercise.objects.recompute_solved_by()
        self.stdout.write("Recomputing teams scores...")
        Team.objects.recompute_ranks()
        self.stdout.write("Recomputing users points...")
        UserInfo.objects.recompute_points()
        self.stdout.write(self.style.SUCCESS("Successfully recomputed all stats"))

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from website.models import UserStats, Exercise


class Command(BaseCommand):
    help = "Recompute all user stats"

    def handle(self, *args, **options):
        for user in User.objects.all():
            user_stats, _ = UserStats.objects.get_or_create(user=user)
            user_stats.points = sum(
                bool(exercise.user_successes)
                for exercise in Exercise.objects.with_user_stats(user=user)
            )
            user_stats.save()
        self.stdout.write(self.style.SUCCESS("Successfully recomputed all stats"))

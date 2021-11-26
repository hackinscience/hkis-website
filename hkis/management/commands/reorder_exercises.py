from django.core.management.base import BaseCommand
from website.models import Exercise


class Command(BaseCommand):
    help = "Reorder all exercises according to their number of solves."

    def handle(self, *args, **options):
        Exercise.objects.reorganize()
        self.stdout.write(self.style.SUCCESS("Successfully reorganized all exercises"))

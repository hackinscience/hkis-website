from django.core.management.base import BaseCommand
from hkis.models import Exercise
from django.db.models import Min


class Command(BaseCommand):
    help = "Infer exercises created_at from answers."

    def handle(self, *args, **options):
        for exercise in Exercise.objects.annotate(
            first_answer=Min("answers__created_at")
        ):
            if exercise.first_answer:
                exercise.created_at = exercise.first_answer
                exercise.save()
        self.stdout.write(self.style.SUCCESS("Done."))

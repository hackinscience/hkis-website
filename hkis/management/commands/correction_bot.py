from django.core.management.base import BaseCommand
import subprocess


class Command(BaseCommand):
    help = "Run a correction bot process"

    def handle(self, *args, **options):
        subprocess.run(["celery", "-A", "hkis.tasks", "worker"])

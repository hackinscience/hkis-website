from django.core.management.base import BaseCommand
from hkis.models import User, UserInfo


class Command(BaseCommand):
    help = "Sync hkis_user to hkis_userinfo"

    def handle(self, *args, **options):
        for user in User.objects.all():
            UserInfo.objects.get_or_create(user=user)
            user.hkis.rank = user.rank
            user.hkis.points = user.points
            user.save()

        self.stdout.write(self.style.SUCCESS("Successfully synchronized"))

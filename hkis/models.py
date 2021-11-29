import logging
from datetime import timedelta

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models, IntegrityError
from django.db.models import Count, Value, Q, Min, Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.defaultfilters import truncatechars
from django.urls import reverse
from django.utils.text import Truncator
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import AutoSlugField


logger = logging.getLogger(__name__)


User = get_user_model()


class UserInfoQuerySet(models.QuerySet):
    def recompute_ranks(self):  # pylint: disable=no-self-use
        for userinfo in UserInfo.objects.order_by("rank"):
            userinfo.recompute_rank()


class UserInfo(models.Model):
    objects = UserInfoQuerySet.as_manager()
    user = models.OneToOneField(to=User, on_delete=models.CASCADE, related_name="hkis")
    points = models.FloatField(default=0)  # Computed sum of solved exercise positions.
    rank = models.PositiveIntegerField(blank=True, null=True)
    public_profile = models.BooleanField(default=True)

    def public_teams(self):
        return self.user.teams.filter(is_public=True)

    def recompute_rank(self) -> int:
        """Reconpute, and return, the user rank.

        Points for one exercise done:

        - Equals to the position of the exercise, itself often equal
          to number_of_solves_of_easiest_exercise - number_of_solve

        - Solving it "late" remove points, but doing more exercise
          should always grant more than doing them first!

        - Only less than one point can be lost by doing it late, so it
          won't appear visually when ceil()ed, but make 1st solver 1st
          in the leaderboard.
        """
        points = 0
        for exercise in Exercise.objects.with_user_stats(user=self.user).only(
            "points", "created_at"
        ):
            if exercise.user_successes:
                time_to_solve = (
                    exercise.solved_at - exercise.created_at
                ).total_seconds()
                points += exercise.points - (time_to_solve ** 0.001 - 1)
        self.points = points
        self.rank = UserInfo.objects.filter(points__gt=self.points).count() + 1
        self.save()
        return self.rank


class Page(models.Model):
    slug = models.CharField(max_length=64)
    title = models.CharField(max_length=512)
    body = models.TextField(default="", blank=True)
    position = models.FloatField(default=0, blank=True)
    in_menu = models.BooleanField(default=False, blank=True)

    def get_absolute_url(self):
        return reverse("page", args=[self.slug])

    def __str__(self):
        return self.title


class Category(models.Model):
    class Meta:
        verbose_name_plural = "Categories"

    title = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from=["title"], editable=True)
    created_at = models.DateTimeField(auto_now_add=True)
    position = models.FloatField(default=0)

    def __str__(self):
        return self.title or self.title_en or "Unnamed"  # pylint: disable=no-member


class ExerciseQuerySet(models.QuerySet):
    def reorganize(self):
        all_exercises = self.with_global_stats()
        max_solves = max(exercise.successes for exercise in all_exercises)
        number_of_exercises = len(all_exercises)
        for i, exercise in enumerate(all_exercises):
            exercise.position = (
                1 + max_solves - exercise.successes + i / number_of_exercises
            )
            exercise.save()

    def with_global_stats(self):
        return self.annotate(
            tries=Count("answers__user", distinct=True),
            successes=Count(
                "answers__user", filter=Q(answers__is_valid=True), distinct=True
            ),
        )

    def with_user_stats(self, user):
        if user.is_anonymous:
            return self.annotate(
                user_tries=Value(0, models.IntegerField()),
                solved_at=Value(now(), models.DateTimeField()),
                user_successes=Value(0, models.IntegerField()),
            )
        return self.annotate(
            user_tries=Count("answers", filter=Q(answers__user=user)),
            solved_at=Min("answers__created_at", filter=Q(answers__user=user)),
            user_successes=Count(
                "answers",
                filter=Q(answers__user=user) & Q(answers__is_valid=True),
            ),
        )

    def with_monthly_stats(self):
        return self.annotate(
            last_month_tries=Count(
                "answers__user",
                filter=Q(
                    answers__created_at__gt=now() - timedelta(days=30),
                    answers__user__is_staff=False,
                ),
                distinct=True,
            ),
            prev_month_tries=Count(
                "answers__user",
                filter=Q(
                    answers__created_at__gt=now() - timedelta(days=60),
                    answers__created_at__lt=now() - timedelta(days=30),
                    answers__user__is_staff=False,
                ),
                distinct=True,
            ),
            last_month_successes=Count(
                "answers__user",
                filter=Q(
                    answers__is_valid=True,
                    answers__user__is_staff=False,
                    answers__created_at__gt=now() - timedelta(days=30),
                ),
                distinct=True,
            ),
            prev_month_successes=Count(
                "answers__user",
                filter=Q(
                    answers__is_valid=True,
                    answers__user__is_staff=False,
                    answers__created_at__gt=now() - timedelta(days=60),
                    answers__created_at__lt=now() - timedelta(days=30),
                ),
                distinct=True,
            ),
        )


class Exercise(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    slug = AutoSlugField(populate_from=["title"], editable=True)
    # pre_check is ran out of the sandbox (with network access and
    # all) before the check. It has the LANGUAGE env set to the user
    # preferences, and current working directory in a directory with
    # `check.py` and `solution` already present, but nothing more,
    # like when check runs.
    pre_check = models.TextField(blank=True, null=True)
    # check is ran inside the sandbox, in a `check.py` file, near a
    # `solution` file containing the student code.
    check = models.TextField(blank=True, default="")
    is_published = models.BooleanField(default=False)
    wording = models.TextField(blank=True, default="")
    initial_solution = models.TextField(blank=True, default="")
    position = models.FloatField(default=0)
    objects = ExerciseQuerySet.as_manager()
    created_at = models.DateTimeField(auto_now_add=True)
    # Number of points are granted for solving this exercise
    points = models.IntegerField(default=1)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, blank=True, null=True
    )
    page = models.ForeignKey(Page, on_delete=models.RESTRICT, related_name="exercises")

    def shared_solutions(self):
        return Answer.objects.filter(
            exercise=self, is_valid=True, is_shared=True
        ).order_by("user__hkis__rank")

    def is_solved_by(self, user):
        return self.answers.filter(user=user, is_valid=True).exists()

    def clean(self):
        """Clean windows-style newlines, maybe inserted by Ace editor, or
        other users.
        """
        self.check = self.check.replace("\r\n", "\n")
        self.wording = self.wording.replace("\r\n", "\n")
        if self.is_published:
            if not self.check:
                raise ValidationError(
                    _("Exercises should have a check script in order to be published.")
                )
            if not self.wording:
                raise ValidationError(
                    _("Exercises should have a wording in order to be published.")
                )

    class Meta:
        ordering = ("category__position", "category", "position")

    def get_absolute_url(self):
        return reverse("exercise", args=[self.page.slug, self.slug])

    def get_solutions_absolute_url(self):
        return reverse("solutions", args=[self.page.slug, self.slug])

    def __str__(self):
        return self.title


class Answer(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=["exercise", "-votes"]),
            models.Index(fields=["is_valid", "is_safe"]),
        ]

    exercise = models.ForeignKey(
        Exercise, on_delete=models.CASCADE, related_name="answers"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, editable=False, null=True, blank=True
    )
    source_code = models.TextField()
    is_corrected = models.BooleanField(default=False)
    is_valid = models.BooleanField(default=False)
    is_shared = models.BooleanField(default=False)
    correction_message = models.TextField(default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    corrected_at = models.DateTimeField(blank=True, null=True)
    is_unhelpfull = models.BooleanField(default=False, blank=True)
    votes = models.IntegerField(default=0, blank=True, null=False)  # Sum of Vote.value
    is_safe = models.BooleanField(
        default=False, blank=True
    )  # If answer can be used without sandboxing for test purposes. To be set manually.

    def short_correction_message(self):
        return truncatechars(self.correction_message.strip().split("\n")[0], 100)

    def __str__(self):
        return "{} on {}".format(
            Truncator(self.user.username if self.user else "Anon").chars(30),
            self.exercise.title,
        )

    def get_absolute_url(self):
        return self.exercise.get_absolute_url() + "?view_as=" + str(self.user.id)

    def save(self, *args, **kwargs):
        if self.correction_message and self.correction_message.startswith("Traceback"):
            self.is_unhelpfull = True
        super().save(*args, **kwargs)

    def send_to_correction_bot(self, lang="en"):
        from hkis.tasks import check_answer  # pylint: disable=import-outside-toplevel

        sync_check_answer = async_to_sync(check_answer)
        is_valid, message = sync_check_answer(
            {
                "check": self.exercise.check,
                "pre_check": self.exercise.pre_check,
                "source_code": self.source_code,
                "language": lang,
            }
        )
        self.correction_message = message
        self.is_corrected = True
        self.is_valid = is_valid
        self.corrected_at = now()
        self.save()


class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    value = models.IntegerField(null=False)  # Typically +1 or -1


@receiver(post_save, sender=Vote)
def update_vote_count(sender, instance, **kwargs):  # pylint: disable=unused-argument
    instance.answer.votes = Vote.objects.filter(answer=instance.answer).aggregate(
        Sum("value")
    )["value__sum"]
    instance.answer.save()


class TeamQuerySet(models.QuerySet):
    def my_teams(self, user):
        """Get teams for which user is staff."""
        return self.filter(
            Q(membership__role=Membership.Role.STAFF) & Q(membership__user=user)
        )

    def recompute_ranks(self):  # pylint: disable=no-self-use
        for team in Team.objects.all():
            team.recompute_rank()


class Team(models.Model):
    objects = TeamQuerySet.as_manager()
    name = models.CharField(max_length=42, unique=True)
    slug = AutoSlugField(populate_from=["name"], editable=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(User, through="Membership", related_name="teams")
    is_public = models.BooleanField(default=True)
    points = models.FloatField(default=0)  # Computed value trying to represent the team

    def recompute_rank(self):
        """Try to mix member score to get a representative team score."""
        values = 0
        weights = 1  # Won't change much big teams, but penalize too-small teams.
        i = 1
        for member in (
            self.membership_set.filter(
                Q(role=Membership.Role.STAFF) | Q(role=Membership.Role.MEMBER)
            )
            .filter(user__hkis__isnull=False)
            .select_related("user__hkis")
            .order_by("user__hkis__points")
        ):
            values += member.user.hkis.points * i
            weights += i
            i += i
        try:
            self.points = values / weights
        except ZeroDivisionError:
            self.points = 0
        self.save()

    def is_staff(self, user):
        return self.membership_set.filter(
            user=user, role=Membership.Role.STAFF
        ).exists()

    def add_member(self, username):
        """Join a team.

        If the team has no staff yet, join as staff, else join as
        pending member.
        """
        role = (
            Membership.Role.STAFF
            if not self.membership_set.filter(role=Membership.Role.STAFF).exists()
            else Membership.Role.PENDING
        )
        try:
            return Membership.objects.create(
                team=self, user=User.objects.get(username=username), role=role
            )
        except IntegrityError:  # Already member of the team.
            return None

    def remove_member(self, username):
        """Remove a member from the team.

        If no staff remain after removal, elect a new staff.

        If no member left after removal, remove the team.
        """
        self.membership_set.filter(user__username=username).delete()
        # If there's no more staff, pick oldest member as staff:
        if not self.membership_set.filter(role=Membership.Role.STAFF):
            for membership in self.membership_set.filter(
                role=Membership.Role.MEMBER
            ).order_by("-created_at"):
                membership.role = Membership.Role.STAFF
                membership.save()
                break
            # No member to grant?
            # Last resort: Pick a pending member as new staff:
            for membership in self.membership_set.order_by("-created_at"):
                membership.role = Membership.Role.STAFF
                membership.save()
                break
            # No member left at all? Drop the team.
            self.delete()

    def accept(self, username):
        membership = self.membership_set.get(user__username=username)
        membership.role = Membership.Role.MEMBER
        membership.save()

    def members_by_rank(self):
        return (
            self.membership_set.filter(user__hkis__isnull=False)
            .order_by("user__hkis__rank")
            .select_related("user__hkis")
        )

    def __str__(self):
        return self.name


class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["user", "team"]]

    class Role(models.TextChoices):
        PENDING = "PE", _("Pending")
        MEMBER = "MM", _("Member")
        STAFF = "ST", _("Staff")

    def __str__(self):
        return f"{self.user.username} in {self.team.name}"

    role = models.CharField(
        max_length=2,
        choices=Role.choices,
        default=Role.MEMBER,
    )

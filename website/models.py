import logging
from datetime import timedelta

import django.contrib.auth.models
from django.db import models
from django.db.models import Count, Value, Q, Min
from django.urls import reverse
from django.utils.text import Truncator
from django.utils.timezone import now
from django_extensions.db.fields import AutoSlugField

logger = logging.getLogger(__name__)


class UserManager(django.contrib.auth.models.UserManager):
    def recompute_ranks(self):
        for user in User.objects.order_by("rank"):
            user.recompute_rank()


class User(django.contrib.auth.models.AbstractUser):
    objects = UserManager()
    points = models.FloatField(default=0)  # Computed sum of solved exercise positions.
    rank = models.PositiveIntegerField(blank=True, null=True)
    public_profile = models.BooleanField(default=True)

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
        for exercise in Exercise.objects.with_user_stats(user=self):
            if exercise.user_successes:
                time_to_solve = (
                    exercise.solved_at - exercise.created_at
                ).total_seconds()
                points += exercise.position - (time_to_solve ** 0.0333 - 1)
        self.points = points
        self.rank = User.objects.filter(points__gt=self.points).count() + 1
        self.save()
        return self.rank


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
    # `check.py` and `solution.py` already present, but nothing more,
    # like when check runs.
    pre_check = models.TextField(blank=True, null=True)
    # check is ran inside the sandbox, in a `check.py` file, near a
    # `solution.py` file containing the student code.
    check = models.TextField()
    is_published = models.BooleanField(default=False)
    solution = models.TextField()
    wording = models.TextField()
    initial_solution = models.TextField(blank=True)
    position = models.FloatField(default=0)
    objects = ExerciseQuerySet.as_manager()
    created_at = models.DateTimeField(auto_now_add=True)
    # Number of points are granted for solving this exercise
    points = models.IntegerField(default=1)

    def clean_fields(self, exclude=None):
        """Clean windows-style newlines, maybe inserted by Ace editor, or
        other users.
        """
        if "check" not in exclude:
            self.check = self.check.replace("\r\n", "\n")
        if "solution" not in exclude:
            self.solution = self.solution.replace("\r\n", "\n")
        if "wording" not in exclude:
            self.wording = self.wording.replace("\r\n", "\n")

    class Meta:
        ordering = ["position"]

    def get_absolute_url(self):
        return reverse("exercise", args=[self.slug])

    def __str__(self):
        return self.title


class Snippet(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, editable=False, blank=True, null=True
    )
    source_code = models.TextField()
    output = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    executed_at = models.DateTimeField(blank=True, null=True)

    def short_input(self):
        return self.source_code.split("\n")[:1][:100]

    def short_output(self):
        return self.output.split("\n")[:1][:100]


class Answer(models.Model):
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

    def short_correction_message(self):
        return self.correction_message.strip().split("\n")[:1][:100]

    def __str__(self):
        return "{} on {}".format(
            Truncator(self.user.username if self.user else "Anon").chars(30),
            self.exercise.title,
        )

    def get_absolute_url(self):
        return reverse("exercise", args=[self.exercise.slug])

    def save(self, *args, **kwargs):
        if self.correction_message and self.correction_message.startswith("Traceback"):
            self.is_unhelpfull = True
        super().save(*args, **kwargs)

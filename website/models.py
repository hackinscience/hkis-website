import logging
from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count, IntegerField, Value, Q
from django.db.models.signals import post_save
from django.urls import reverse
from django.utils.text import Truncator
from django.utils.timezone import now
from django.utils import translation
from django_extensions.db.fields import AutoSlugField
from rest_framework import serializers

logger = logging.getLogger(__name__)


class ExerciseQuerySet(models.QuerySet):
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
                user_tries=Value(0, IntegerField()),
                user_successes=Value(0, IntegerField()),
            )
        return self.annotate(
            user_tries=Count("answers", filter=Q(answers__user=user)),
            user_successes=Count(
                "answers",
                filter=Q(answers__user=user) & Q(answers__is_valid=True),
            ),
        )

    def with_weekly_stats(self):
        return self.annotate(
            last_week_tries=Count(
                "answers__user",
                filter=Q(
                    answers__created_at__gt=now() - timedelta(days=7),
                    answers__user__is_staff=False,
                ),
                distinct=True,
            ),
            prev_week_tries=Count(
                "answers__user",
                filter=Q(
                    answers__created_at__gt=now() - timedelta(days=14),
                    answers__created_at__lt=now() - timedelta(days=7),
                    answers__user__is_staff=False,
                ),
                distinct=True,
            ),
            last_week_successes=Count(
                "answers__user",
                filter=Q(
                    answers__is_valid=True,
                    answers__user__is_staff=False,
                    answers__created_at__gt=now() - timedelta(days=7),
                ),
                distinct=True,
            ),
            prev_week_successes=Count(
                "answers__user",
                filter=Q(
                    answers__is_valid=True,
                    answers__user__is_staff=False,
                    answers__created_at__gt=now() - timedelta(days=14),
                    answers__created_at__lt=now() - timedelta(days=7),
                ),
                distinct=True,
            ),
        )


class UserStatsQuerySet(models.QuerySet):
    def recompute(self):
        for user in User.objects.all():
            user_stats, _ = UserStats.objects.get_or_create(user=user)
            user_stats.recompute()


class UserStats(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    points = models.FloatField(default=0)  # Computed sum of solved exercise positions.
    rank = models.PositiveIntegerField(blank=True, null=True)
    objects = UserStatsQuerySet.as_manager()

    def recompute(self):
        self.points = sum(
            exercise.position
            for exercise in Exercise.objects.with_user_stats(user=self.user)
            if exercise.user_successes
        )
        self.save()
        self.rank = UserStats.objects.filter(points__gt=self.points).count() + 1
        self.save()


class Exercise(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    slug = AutoSlugField(populate_from=["title"], editable=True)
    check = models.TextField()
    is_published = models.BooleanField(default=False)
    solution = models.TextField()
    wording = models.TextField()
    initial_solution = models.TextField(blank=True)
    position = models.FloatField(default=0)
    objects = ExerciseQuerySet.as_manager()

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
    user = models.ForeignKey(User, on_delete=models.CASCADE, editable=False)
    source_code = models.TextField()
    is_corrected = models.BooleanField(default=False)
    is_valid = models.BooleanField(default=False)
    is_shared = models.BooleanField(default=False)
    correction_message = models.TextField(default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    corrected_at = models.DateTimeField(blank=True, null=True)

    def short_correction_message(self):
        return self.correction_message.strip().split("\n")[:1][:100]

    def __str__(self):
        return "{} on {}".format(
            Truncator(self.user.username).chars(30), self.exercise.title
        )

    def get_absolute_url(self):
        return reverse("exercise", args=[self.exercise.slug])


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = "__all__"


class SnippetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Snippet
        fields = "__all__"


def cb_new_answer(sender, instance, created, **kwargs):
    group = f"user.{instance.user.id}.ex.{instance.exercise.id}"
    message = AnswerSerializer(instance).data
    if instance.is_valid:
        user_stats, _ = UserStats.objects.get_or_create(user=instance.user)
        user_stats.recompute()
        message["user_rank"] = user_stats.rank
    channel_layer = get_channel_layer()
    message["type"] = "answer.update"
    logger.info("New answer notification for user %s", instance.user.id)
    async_to_sync(channel_layer.group_send)(group, message)


post_save.connect(cb_new_answer, sender=Answer)

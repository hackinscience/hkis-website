import logging
from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count, Q
from django.db.models.signals import post_save
from django.urls import reverse
from django.utils.text import Truncator
from django.utils.timezone import now
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
        return self.annotate(
            user_tries=Count("answers", filter=Q(answers__user=user)),
            user_successes=Count(
                "answers", filter=Q(answers__user=user) & Q(answers__is_valid=True),
            ),
        )

    def with_weekly_stats(self):
        return self.annotate(
            last_week_tries=Count(
                "answers__user",
                filter=Q(answers__created_at__gt=now() - timedelta(days=7)),
                distinct=True,
            ),
            last_week_successes=Count(
                "answers__user",
                filter=Q(
                    answers__is_valid=True,
                    answers__created_at__gt=now() - timedelta(days=7),
                ),
                distinct=True,
            ),
        )


class Exercise(models.Model):
    title = models.CharField(max_length=255)
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, editable=False)
    source_code = models.TextField()
    output = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    executed_at = models.DateTimeField(blank=True, null=True)

    def short_input(self):
        return self.source_code.split("\n")[:1][:100]

    def short_output(self):
        return self.output.split("\n")[:1][:100]


class AnswerQuerySet(models.QuerySet):
    def shared(self, exercise_id):
        queryset = self.filter(
            exercise__pk=exercise_id, is_valid=True, is_shared=True
        ).order_by("-created_at")
        if settings.DATABASES[self.db]["ENGINE"].endswith("postgresql"):
            queryset = queryset.distinct("source_code")
        return queryset


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
    objects = AnswerQuerySet.as_manager()

    def short_correction_message(self):
        return self.correction_message.split("\n")[:1][:100]

    def __str__(self):
        return "{} on {}".format(
            Truncator(self.user.username).chars(30), self.exercise.title
        )

    def get_absolute_url(self):
        return reverse("exercise", args=[self.exercise.slug])


class Lesson(models.Model):
    title = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from=["title"], editable=True)
    content = models.TextField()
    is_published = models.BooleanField(default=False)
    position = models.FloatField(default=0)

    class Meta:
        ordering = ["position"]

    def get_absolute_url(self):
        return reverse("lesson", args=[self.slug])

    def __str__(self):
        return self.title


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
    channel_layer = get_channel_layer()
    message = AnswerSerializer(instance).data
    message["type"] = "answer.update"
    logger.info("New answer notification for user %s", instance.user.id)
    async_to_sync(channel_layer.group_send)(group, message)


post_save.connect(cb_new_answer, sender=Answer)

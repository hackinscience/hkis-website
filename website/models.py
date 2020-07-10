import logging
from asgiref.sync import async_to_sync
from django.db import models
from django.db.models import Count, Q
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models.signals import post_save
from channels.layers import get_channel_layer
from django_extensions.db.fields import AutoSlugField


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
        return self.correction_message.split("\n")[:1][:100]

    def __str__(self):
        return "{} on {}".format(self.user.username, self.exercise.title)

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


def cb_new_snippet(sender, instance, created, **kwargs):
    group = "snippets.{}".format(instance.user.id)
    logger.info("New snippet notification for user %s", instance.user.id)
    snippet = {"type": "snippet", "id": instance.id, "output": instance.output}

    if instance.executed_at:
        snippet["executed_at"] = instance.executed_at.isoformat()

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(group, snippet)


post_save.connect(cb_new_snippet, sender=Snippet)

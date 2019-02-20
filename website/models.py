import logging
from asgiref.sync import async_to_sync
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models.signals import post_save
from channels.layers import get_channel_layer
from django_extensions.db.fields import AutoSlugField


logger = logging.getLogger(__name__)


class Exercise(models.Model):
    title = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from=["title"], editable=True)
    check = models.TextField()
    is_published = models.BooleanField(default=False)
    solution = models.TextField()
    wording = models.TextField()
    initial_solution = models.TextField(default="#!/usr/bin/env python3\n\n")
    position = models.FloatField(default=0)

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

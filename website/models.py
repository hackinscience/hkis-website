from asgiref.sync import async_to_sync
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.timezone import now
from django.db.models.signals import post_save
from channels.layers import get_channel_layer
from django_extensions.db.fields import AutoSlugField


class Exercise(models.Model):
    title = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from=['title'], editable=True)
    check = models.TextField()
    solution = models.TextField()
    wording = models.TextField()
    initial_solution = models.TextField(default="#!/usr/bin/env python3\n\n")
    position = models.FloatField(default=0)

    class Meta:
        ordering = ["position"]

    def __str__(self):
        return self.title


class Snippet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, editable=False)
    source_code = models.TextField()
    output = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    executed_at = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.output and not self.executed_at:
            self.executed_at = now()
        super().save(*args, **kwargs)


class Answer(models.Model):
    exercise = models.ForeignKey(
        Exercise, on_delete=models.CASCADE, related_name="answers"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, editable=False)
    source_code = models.TextField()
    is_corrected = models.BooleanField(default=False)
    is_valid = models.BooleanField(default=False)
    correction_message = models.TextField(default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    corrected_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return "{} on {}".format(self.user.username, self.exercise.title)

    def get_absolute_url(self):
        return reverse("exercise", args=[self.exercise.id])


def cb_new_answer(sender, instance, created, **kwargs):
    group = "answers.{}.{}".format(instance.user.id, instance.exercise.id)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "correction",
            "exercise": instance.exercise.id,
            "correction_message": instance.correction_message,
            "answer": instance.id,
            "is_corrected": instance.is_corrected,
        },
    )


def cb_new_snippet(sender, instance, created, **kwargs):
    group = "snippets.{}".format(instance.user.id)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group, {"type": "snippet", "id": instance.id, "output": instance.output}
    )


post_save.connect(cb_new_answer, sender=Answer)
post_save.connect(cb_new_snippet, sender=Snippet)

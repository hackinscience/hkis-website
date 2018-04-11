from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from notifications.signals import notify
from django.db.models.signals import post_save

class Exercise(models.Model):
    title = models.CharField(max_length=255)
    check = models.TextField()
    solution = models.TextField()
    wording = models.TextField()

    def __str__(self):
        return self.title

class Answer(models.Model):
    exercise = models.ForeignKey(Exercise,
            on_delete=models.CASCADE,
            related_name="answers")
    user = models.ForeignKey(User,
            on_delete=models.CASCADE,
            editable=False)
    source_code = models.TextField()
    is_corrected = models.BooleanField(default=False)
    is_valid = models.BooleanField(default=False)
    correction_message = models.TextField(default='', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    corrected_at = models.DateTimeField(blank=True, null=True)

    def get_absolute_url(self):
        return reverse('exercise', args=[self.exercise.id])


def new_answer(sender, instance, created, **kwargs):
    if instance.is_corrected:
        notify.send(instance,
                recipient=instance.user,
                verb=instance.correction_message)

post_save.connect(new_answer, sender=Answer)

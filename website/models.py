from django.db import models
from django.contrib.auth.models import User

class Exercise(models.Model):
    title = models.CharField(max_length=255)
    check = models.TextField()
    solution = models.TextField()
    wording = models.TextField()

class Answer(models.Model):
    exercise = models.ForeignKey(Exercise,
            on_delete=models.CASCADE,
            related_name="answers")
    user = models.ForeignKey(User,
            on_delete=models.CASCADE)
    source_code = models.TextField()
    is_corrected = models.BooleanField()
    is_valid = models.BooleanField()
    correction_message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    corrected_at = models.DateTimeField()

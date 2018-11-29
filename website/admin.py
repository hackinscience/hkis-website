from django import forms
from django.contrib import admin
from django_ace import AceWidget
from website.models import Answer, Exercise
from website.forms import AnswerForm


class AdminExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = "__all__"
        widgets = {
            "solution": AceWidget(
                mode="python", theme="twilight", width="800px", height="400px"
            ),
            "check": AceWidget(
                mode="python", theme="twilight", width="800px", height="400px"
            ),
            "wording": AceWidget(
                mode="markdown", theme="twilight", width="800px", height="400px"
            ),
        }


class ExerciseAdmin(admin.ModelAdmin):
    readonly_fields = ("id",)
    list_display = ("title", "position")
    form = AdminExerciseForm


class AnswerAdmin(admin.ModelAdmin):
    readonly_fields = ("user",)


admin.site.register(Answer, AnswerAdmin)
admin.site.register(Exercise, ExerciseAdmin)

from django import forms
from django.contrib import admin
from django_ace import AceWidget
from website.models import Answer, Exercise, Snippet
from website.forms import AnswerForm


class AdminExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = (
            "title",
            "position",
            "wording",
            "initial_solution",
            "check",
            "solution",
        )
        widgets = {
            "solution": AceWidget(
                mode="python", theme="twilight", width="100%", height="400px"
            ),
            "check": AceWidget(
                mode="python", theme="twilight", width="100%", height="400px"
            ),
            "wording": AceWidget(
                mode="markdown", theme="twilight", width="100%", height="800px"
            ),
            "initial_solution": AceWidget(
                mode="python", theme="twilight", width="100%", height="400px"
            ),
        }


class ExerciseAdmin(admin.ModelAdmin):
    readonly_fields = ("id",)
    list_display = ("title", "position")
    form = AdminExerciseForm


class AnswerAdmin(admin.ModelAdmin):
    readonly_fields = ("user", "created_at", "corrected_at")
    list_display = ("user", "exercise", "is_valid", "created_at", "is_corrected")
    list_filter = ("is_corrected", "is_valid")
    search_fields = ("user__username",)


class SnippetAdmin(admin.ModelAdmin):
    readonly_fields = ("user", "created_at", "executed_at")
    list_display = ("user", "created_at", "executed_at")
    search_fields = ("user__username",)


admin.site.register(Answer, AnswerAdmin)
admin.site.register(Exercise, ExerciseAdmin)
admin.site.register(Snippet, SnippetAdmin)

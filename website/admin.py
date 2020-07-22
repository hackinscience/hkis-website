from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django_ace import AceWidget

from website.models import Answer, Exercise, Snippet


class AdminExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = (
            "title",
            "slug",
            "author",
            "is_published",
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


class AnswerExerciseForm(forms.ModelForm):
    class Meta:
        model = Answer
        exclude = tuple()
        widgets = {
            "source_code": AceWidget(
                mode="python", theme="twilight", width="100%", height="400px"
            ),
            "correction_message": AceWidget(
                mode="markdown", theme="twilight", width="100%", height="400px"
            ),
        }


class ExerciseAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).with_weekly_stats()

    ordering = ("-is_published", "position")
    readonly_fields = ("id",)
    list_display = (
        "title",
        "position",
        "weekly_tries",
        "weekly_successes",
        "weekly_success_ratio",
        "is_published",
    )

    def weekly_tries(self, obj):
        return f"{obj.last_week_tries} ({obj.last_week_tries - obj.prev_week_tries:+})"

    def weekly_successes(self, obj):
        return f"{obj.last_week_successes} ({obj.last_week_successes - obj.prev_week_successes:+})"

    def weekly_success_ratio(self, obj):
        last_week_ratio = prev_week_ratio = None
        if obj.last_week_successes:
            last_week_ratio = obj.last_week_successes / obj.last_week_tries
        if obj.prev_week_successes:
            prev_week_ratio = obj.prev_week_successes / obj.prev_week_tries
        if prev_week_ratio is not None and last_week_ratio is not None:
            return f"{last_week_ratio:.0%} ({100*(last_week_ratio - prev_week_ratio):+.2f})"
        if last_week_ratio is not None:
            return f"{last_week_ratio:.0%}"
        else:
            return "ø"

    form = AdminExerciseForm


class AnswerAdmin(admin.ModelAdmin):
    readonly_fields = ("user", "created_at", "corrected_at")
    list_display = (
        "__str__",
        "short_correction_message",
        "is_valid",
        "is_corrected",
        "is_shared",
        "created_at",
    )
    list_filter = ("is_corrected", "is_valid", "is_shared")
    search_fields = ("user__username",)
    form = AnswerExerciseForm


class SnippetAdmin(admin.ModelAdmin):
    readonly_fields = ("user", "created_at", "executed_at")
    list_display = ("user", "short_input", "short_output", "created_at", "executed_at")
    search_fields = ("user__username",)


class MyUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ("date_joined", "points", "rank")
    ordering = ("-date_joined",)

    def points(self, obj):
        return obj.userstats.points

    def rank(self, obj):
        return obj.userstats.rank

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("userstats")


admin.site.register(Answer, AnswerAdmin)
admin.site.register(Exercise, ExerciseAdmin)
admin.site.register(Snippet, SnippetAdmin)

admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)

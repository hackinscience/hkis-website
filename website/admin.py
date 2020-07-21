from django import forms
from django.contrib import admin
from django_ace import AceWidget
from website.models import Answer, Exercise, Snippet, Lesson
from registration.admin import RegistrationAdmin
from registration.models import RegistrationProfile
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User


class AdminExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = (
            "title",
            "slug",
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


class AdminLessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ("title", "slug", "is_published", "position", "content")
        widgets = {
            "content": AceWidget(
                mode="markdown", theme="twilight", width="100%", height="800px"
            )
        }


class ExerciseAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).with_weekly_stats()

    readonly_fields = ("id",)
    list_display = (
        "title",
        "slug",
        "is_published",
        "position",
        "last_week_tries",
        "last_week_successes",
    )

    def last_week_tries(self, obj):
        """Without this, I'm getting:

        (admin.E108) The value of 'list_display[4]' refers to 'tries',
        which is not a callable, an attribute of 'ExerciseAdmin', or
        an attribute or method on 'website.Exercise'.

        Maybe the system check don't see my get_queryset?
        """
        return obj.last_week_tries

    def last_week_successes(self, obj):
        return obj.last_week_successes

    form = AdminExerciseForm


class LessonAdmin(admin.ModelAdmin):
    readonly_fields = ("id",)
    list_display = ("title", "slug", "is_published", "position")
    form = AdminLessonForm


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


class MyRegistrationAdmin(RegistrationAdmin):
    list_display = RegistrationAdmin.list_display + ("activated",)


class MyUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ("date_joined",)


admin.site.register(Answer, AnswerAdmin)
admin.site.register(Exercise, ExerciseAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Snippet, SnippetAdmin)

admin.site.unregister(RegistrationProfile)
admin.site.register(RegistrationProfile, MyRegistrationAdmin)

admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)

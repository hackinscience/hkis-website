from django import forms
from django.contrib import admin
from django_ace import AceWidget
from website.models import Answer, Exercise, Snippet
from website.forms import AnswerForm
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


class ExerciseAdmin(admin.ModelAdmin):
    readonly_fields = ("id",)
    list_display = ("title", "slug", "is_published", "position")
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


class MyRegistrationAdmin(RegistrationAdmin):
    list_display = RegistrationAdmin.list_display + ("activated",)


class MyUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ("date_joined",)


admin.site.register(Answer, AnswerAdmin)
admin.site.register(Exercise, ExerciseAdmin)
admin.site.register(Snippet, SnippetAdmin)

admin.site.unregister(RegistrationProfile)
admin.site.register(RegistrationProfile, MyRegistrationAdmin)

admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)

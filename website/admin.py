from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import reverse
from django.utils.safestring import mark_safe
from django_ace import AceWidget

from modeltranslation.admin import TranslationAdmin

from website.models import Answer, Exercise, Snippet, User, Team, Membership


class AdminExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        exclude = ()
        widgets = {
            "solution": AceWidget(
                mode="python", theme="twilight", width="100%", height="400px"
            ),
            "check": AceWidget(
                mode="python", theme="twilight", width="100%", height="400px"
            ),
            "pre_check": AceWidget(
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
        exclude = ()
        widgets = {
            "source_code": AceWidget(
                mode="python", theme="twilight", width="100%", height="400px"
            ),
            "correction_message": AceWidget(
                mode="markdown", theme="twilight", width="100%", height="400px"
            ),
        }


class ExerciseAdmin(TranslationAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).with_monthly_stats()

    ordering = ("-is_published", "position")
    readonly_fields = ("id", "created_at")
    fields = (
        "title",
        "slug",
        "author",
        "created_at",
        "is_published",
        "position",
        "points",
        "wording",
        "initial_solution",
        "pre_check",
        "check",
        "solution",
    )

    list_display = (
        "title",
        "formatted_position",
        "points",
        "monthly_tries",
        "monthly_successes",
        "monthly_success_ratio",
        "is_published",
    )

    def formatted_position(self, obj):
        return f"{obj.position:.2f}"

    formatted_position.short_description = "position"

    def monthly_tries(self, obj):
        return (
            f"{obj.last_month_tries} ({obj.last_month_tries - obj.prev_month_tries:+})"
        )

    def monthly_successes(self, obj):
        return f"{obj.last_month_successes} ({obj.last_month_successes - obj.prev_month_successes:+})"

    def monthly_success_ratio(self, obj):
        last_month_ratio = prev_month_ratio = None
        if obj.last_month_successes:
            last_month_ratio = obj.last_month_successes / obj.last_month_tries
        if obj.prev_month_successes:
            prev_month_ratio = obj.prev_month_successes / obj.prev_month_tries
        if prev_month_ratio is not None and last_month_ratio is not None:
            return f"{last_month_ratio:.0%} ({100*(last_month_ratio - prev_month_ratio):+.2f})"
        if last_month_ratio is not None:
            return f"{last_month_ratio:.0%}"
        else:
            return "ø"

    form = AdminExerciseForm


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 1


class TeamAdmin(admin.ModelAdmin):
    fields = ("name", "is_public")
    readonly_fields = ("created_at",)


class AnswerAdmin(admin.ModelAdmin):
    readonly_fields = ("user", "created_at", "corrected_at")
    list_display = (
        "__str__",
        "short_correction_message",
        "is_valid",
        "is_corrected",
        "is_unhelpfull",
        "created_at",
        "see",
    )
    list_filter = ("is_corrected", "is_valid", "is_shared", "is_unhelpfull")
    search_fields = ("user__username", "exercise__title")
    form = AnswerExerciseForm

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "exercise")

    def see(self, obj):
        url = reverse("exercise", kwargs={"slug": obj.exercise.slug})
        if obj.user:
            return mark_safe(
                f"<a target=_blank href='{url}?view_as={obj.user.id}'>see</a>"
            )
        return ""


class SnippetAdmin(admin.ModelAdmin):
    readonly_fields = ("user", "created_at", "executed_at")
    list_display = ("user", "short_input", "short_output", "created_at", "executed_at")
    search_fields = ("user__username",)


class MyUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ("date_joined", "points", "rank")
    ordering = ("-date_joined",)
    inlines = (MembershipInline,)
    fieldsets = (
        (
            None,
            {"fields": ("username", "password", "public_profile")},
        ),
    ) + UserAdmin.fieldsets[1:]


admin.site.register(Answer, AnswerAdmin)
admin.site.register(Exercise, ExerciseAdmin)
admin.site.register(Snippet, SnippetAdmin)
admin.site.register(User, MyUserAdmin)
admin.site.register(Team, TeamAdmin)

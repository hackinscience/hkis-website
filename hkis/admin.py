from django import forms
from django.core.exceptions import FieldError
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django_ace import AceWidget

from modeltranslation.admin import TranslationAdmin

from hkis.models import (
    Answer,
    Category,
    Exercise,
    Membership,
    Page,
    Team,
    UserInfo,
)


class PageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = ("slug", "title", "body", "position", "in_menu")
        widgets = {
            "body": AceWidget(
                mode="markdown", theme="twilight", width="100%", height="800px"
            ),
        }


class AdminExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = (
            "title",
            "author",
            "slug",
            "pre_check",
            "check",
            "is_published",
            "wording",
            "initial_solution",
            "position",
            "points",
            "category",
            "page",
        )
        widgets = {
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


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = (
            "exercise",
            "source_code",
            "is_corrected",
            "is_valid",
            "is_shared",
            "correction_message",
            "corrected_at",
            "is_unhelpfull",
            "votes",
            "is_safe",
        )
        widgets = {
            "source_code": AceWidget(
                mode="python", theme="twilight", width="100%", height="400px"
            ),
            "correction_message": AceWidget(
                mode="markdown", theme="twilight", width="100%", height="400px"
            ),
        }


class ExerciseAdmin(TranslationAdmin):
    autocomplete_fields = ("author",)
    fields = (
        "title",
        "slug",
        "author",
        "page",
        "category",
        "position",
        "created_at",
        "is_published",
        "points",
        "wording",
        "initial_solution",
        "pre_check",
        "check",
    )
    form = AdminExerciseForm
    list_display = (
        "title",
        "formatted_position",
        "category",
        "points",
        "monthly_tries",
        "monthly_successes",
        "monthly_success_ratio",
        "is_published",
    )
    ordering = ("-is_published", "position")
    readonly_fields = ("id", "created_at")

    def get_queryset(self, request):
        """If not superuser, one can only see own exercises."""
        queryset = super().get_queryset(request).with_monthly_stats()
        if request.user.is_superuser:
            return queryset
        return queryset.filter(author=request.user)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            if not change:
                obj.is_published = False
                obj.author = request.user
                sandbox, _ = Category.objects.get_or_create(
                    title="Sandbox", slug="sandbox", position=999
                )
                obj.category = sandbox
        super().save_formset(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return self.readonly_fields
        return self.readonly_fields + ("author", "category", "is_published")

    @admin.display(description="position")
    def formatted_position(self, obj):  # pylint: disable=no-self-use
        return f"{obj.position:.2f}"

    def monthly_tries(self, obj):  # pylint: disable=no-self-use
        return (
            f"{obj.last_month_tries} ({obj.last_month_tries - obj.prev_month_tries:+})"
        )

    def monthly_successes(self, obj):  # pylint: disable=no-self-use
        return (
            f"{obj.last_month_successes} "
            f"({obj.last_month_successes - obj.prev_month_successes:+})"
        )

    def monthly_success_ratio(self, obj):  # pylint: disable=no-self-use
        last_month_ratio = prev_month_ratio = None
        if obj.last_month_successes:
            last_month_ratio = obj.last_month_successes / obj.last_month_tries
        if obj.prev_month_successes:
            prev_month_ratio = obj.prev_month_successes / obj.prev_month_tries
        if prev_month_ratio is not None and last_month_ratio is not None:
            return (
                f"{last_month_ratio:.0%} "
                f"({100*(last_month_ratio - prev_month_ratio):+.2f})"
            )
        if last_month_ratio is not None:
            return f"{last_month_ratio:.0%}"
        return "ø"


class PageAdmin(TranslationAdmin):
    form = PageForm
    list_display = ("slug", "title")


class MembershipInline(admin.TabularInline):
    model = Membership
    autocomplete_fields = ("user",)
    extra = 1


class TeamAdmin(admin.ModelAdmin):
    fields = ("name", "is_public", "slug")
    list_display = ("name", "points", "members_qty")
    ordering = ("-points",)
    readonly_fields = ("created_at",)
    inlines = (MembershipInline,)

    def members_qty(self, team):  # pylint: disable=no-self-use
        return team.members.count()


@admin.action(description="Send to correction bot")
def send_to_correction_bot(
    modeladmin, request, queryset
):  # pylint: disable=unused-argument
    for answer in queryset:
        answer.send_to_correction_bot()


class TeamFilter(admin.SimpleListFilter):
    title = _("team")
    parameter_name = "team"

    def lookups(self, request, model_admin):
        return [(team.id, team.name) for team in Team.objects.my_teams(request.user)]

    def queryset(self, request, queryset):
        try:  # to filter on objects having a user property:
            if self.value() is not None:
                return queryset.filter(user__teams=self.value())
        except FieldError:  # to filter on users
            if self.value() is not None:
                return queryset.filter(teams=self.value())
        return None


class MyExercisesFilter(admin.SimpleListFilter):
    title = _("exercise author")
    parameter_name = "mine"

    def lookups(self, request, model_admin):
        return [("1", _("My exercises only"))]

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(exercise__author=request.user)
        return queryset


class AnswerAdmin(admin.ModelAdmin):
    readonly_fields = ("user", "created_at", "corrected_at")
    actions = (send_to_correction_bot,)
    list_display = (
        "__str__",
        "short_correction_message",
        "is_valid",
        "is_corrected",
        "is_unhelpfull",
        "created_at",
    )
    list_filter = (
        MyExercisesFilter,
        TeamFilter,
        "is_unhelpfull",
        "is_corrected",
        "is_valid",
        "is_shared",
    )
    search_fields = ("user__username", "exercise__title", "user__teams__name")
    form = AnswerForm

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "exercise")

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None or obj.user is None:
            # obj.user is None in case of an anonymouse user answer.
            return super().has_view_permission(request, obj)
        return super().has_view_permission(request, obj) and (
            obj.exercise.author == request.user
            or (obj.user.teams.all() & Team.objects.my_teams(request.user)).count()
        )

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return super().has_view_permission(request, obj)
        return super().has_change_permission(request, obj) and (
            obj.exercise.author == request.user
            or (obj.user.teams.all() & Team.objects.my_teams(request.user)).count()
        )


class UserInfoAdmin(admin.ModelAdmin):
    list_display = ("user", "points", "rank", "public_profile")
    list_filter = (TeamFilter,)
    search_fields = ("teams__name",)


class CategoryAdmin(TranslationAdmin):
    list_display = ["title", "position"]


admin.site.register(Answer, AnswerAdmin)
admin.site.register(Exercise, ExerciseAdmin)
admin.site.register(UserInfo, UserInfoAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Page, PageAdmin)

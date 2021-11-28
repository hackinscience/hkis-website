from collections import OrderedDict
from contextlib import suppress
from itertools import groupby

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Max, Q
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext
from django.views.decorators.http import require_http_methods
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView
from django.views.generic.list import ListView

from hkis.forms import AnswerForm
from hkis.models import Exercise, Membership, Page, Team, User


def index(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(
            Page.objects.order_by("position")[0].get_absolute_url()
        )
    return render(request, "hkis/index.html")


def old_page(request, url):
    return HttpResponseRedirect("/" + url)


class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ["username", "email"]
    template_name = "hkis/profile_update.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["memberships"] = context["object"].membership_set.all()
        context["exercises"] = Exercise.objects.filter(
            is_published=True
        ).with_user_stats(self.request.user)
        context["done_qty"] = len(
            [ex for ex in context["exercises"] if ex.user_successes]
        )
        context["done_pct"] = (
            f"{context['done_qty'] / len(context['exercises']):.0%}"
            if context["exercises"]
            else "ø"
        )
        context["submit_qty"] = sum(
            exercise.user_tries for exercise in context["exercises"]
        )
        context["participants"] = User.objects.count()
        context["languages"] = settings.LANGUAGES

        return context

    def dispatch(self, request, *args, **kwargs):
        if kwargs["pk"] != request.user.pk:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        messages.info(self.request, "Profile updated")
        return reverse("profile", kwargs={"pk": self.request.user.id})


class Leaderboard(ListView):
    queryset = User.objects.filter(
        hkis__isnull=False, is_superuser=False
    ).select_related("hkis")
    paginate_by = 100
    template_name = "hkis/leaderboard.html"
    ordering = ["-hkis__points"]


class PageView(DetailView):
    model = Page
    slug_url_kwarg = "page"
    template_name = "hkis/page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exercises = (
            self.object.exercises.filter(is_published=True)
            .with_global_stats()
            .with_user_stats(self.request.user)
            .only("title", "category")
            .select_related("category")
        )
        context["by_category"] = [
            (key, list(values))
            for key, values in groupby(
                exercises, key=lambda exercise: exercise.category
            )
        ]
        return context


class ExerciseView(DetailView):
    model = Exercise
    template_name = "hkis/exercise.html"

    def get_object(self, queryset=None):
        """Return the object the view is displaying."""
        # Use a custom queryset if provided; this is required for subclasses
        # like DateDetailView
        if queryset is None:
            queryset = self.get_queryset()
        queryset = queryset.filter(
            page__slug=self.kwargs["page"], slug=self.kwargs["exercise"]
        )
        try:
            # Get the single item from the filtered queryset
            return queryset.get()
        except queryset.model.DoesNotExist as err:
            raise Http404("No exercise found matching the query") from err

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related("author")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["LANGUAGE_CODE"] = self.request.LANGUAGE_CODE
        user = self.request.user
        if self.request.user.is_superuser and self.request.GET.get("view_as"):
            user = User.objects.get(id=self.request.GET.get("view_as"))
            context["is_impersonating"] = user
        if user.is_anonymous:
            context["answers"] = answers = ()
        else:
            context["answers"] = answers = self.object.answers.filter(
                user=user
            ).order_by("-id")
        context["answer_form"] = AnswerForm(
            initial={
                "exercise": "/api/exercises/{}/".format(self.object.id),
                "source_code": answers[0].source_code
                if answers
                else context["exercise"].initial_solution,
            }
        )
        context["object"].wording = gettext(context["object"].wording)
        if user.is_anonymous or not hasattr(user, "hkis"):
            context["current_rank"] = 999999
        else:
            context["current_rank"] = user.hkis.rank
        if user.is_anonymous:
            context["is_valid"] = False
        else:
            context["is_valid"] = bool(
                self.object.answers.filter(user=user, is_valid=True)
            )
        try:
            context["next"] = (
                Exercise.objects.filter(position__gt=self.object.position)
                .filter(is_published=True)
                .order_by("position")[0]
            )
        except IndexError:
            context["next"] = None
        try:
            context["previous"] = Exercise.objects.filter(
                position__lt=self.object.position
            ).order_by("-position")[0]
        except IndexError:
            context["previous"] = None
        return context


class SolutionView(LoginRequiredMixin, DetailView):
    model = Exercise
    template_name = "hkis/solutions.html"

    def get_object(self, queryset=None):
        """Return the object the view is displaying."""
        # Use a custom queryset if provided; this is required for subclasses
        # like DateDetailView
        if queryset is None:
            queryset = self.get_queryset()
        queryset = queryset.filter(
            page__slug=self.kwargs["page"], slug=self.kwargs["exercise"]
        )
        try:
            # Get the single item from the filtered queryset
            return queryset.get()
        except queryset.model.DoesNotExist as err:
            raise Http404("No exercise found matching the query") from err

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["my_answers"] = self.object.answers.filter(
            user=self.request.user
        ).order_by("-created_at")
        if self.object.is_solved_by(self.request.user):
            context["is_solved"] = True
            context["solutions"] = self.object.shared_solutions()[:10]
        else:
            context["is_solved"] = False
            context["solutions"] = []
        try:
            context["next"] = (
                Exercise.objects.filter(position__gt=self.object.position)
                .order_by("position")[0]
                .slug
            )
        except IndexError:
            context["next"] = None
        return context


def team_stats(request, slug):
    try:
        team = Team.objects.get(slug=slug)
    except Team.DoesNotExist as err:
        raise Http404("Team does not exist") from err

    requester_membership = None
    if not request.user.is_anonymous:
        with suppress(Membership.DoesNotExist):
            requester_membership = Membership.objects.get(team=team, user=request.user)
    if not requester_membership:
        raise Http404("Team does not exist")
    if requester_membership.role != Membership.Role.STAFF:
        raise Http404("Team does not exist")

    context = {
        "stats": OrderedDict(
            [
                (
                    user.username,
                    [
                        {
                            "is_tried": exercice.nb_anwser > 0,
                            "is_valid": exercice.nb_valid_anwser > 0,
                            "last_answer": exercice.last_answer,
                            "slug": exercice.slug,
                        }
                        for exercice in Exercise.objects.annotate(
                            last_answer=Max(
                                "answers__pk", filter=Q(answers__user_id=user.id)
                            ),
                            nb_anwser=Count(
                                "answers", filter=Q(answers__user_id=user.id)
                            ),
                            nb_valid_anwser=Count(
                                "answers",
                                filter=Q(answers__is_valid=True)
                                & Q(answers__user_id=user.id),
                            ),
                        ).order_by("position")
                    ],
                )
                for user in User.objects.filter(teams=team).order_by("-points")
            ]
        ),
        "exercises": Exercise.objects.order_by("position"),
    }
    return render(request, "hkis/stats_detail.html", context)


@require_http_methods(["GET", "POST"])
def teams(request):
    if request.method == "POST":
        if request.POST.get("remove_from_team"):
            team = Team.objects.get(name=request.POST["remove_from_team"])
            if team.is_staff(request.user):
                team.remove_member(request.POST["member"])
            return HttpResponseRedirect(reverse("team", kwargs={"slug": team.slug}))
        if request.POST.get("accept_in_team"):
            team = Team.objects.get(name=request.POST["accept_in_team"])
            if team.is_staff(request.user):
                team.accept(request.POST["member"])
            return HttpResponseRedirect(reverse("team", kwargs={"slug": team.slug}))
        if request.POST.get("leave_team"):
            team = Team.objects.get(name=request.POST["leave_team"])
            team.remove_member(request.user.username)
        if request.POST.get("join_team"):
            team, _ = Team.objects.get_or_create(name=request.POST["join_team"])
            team.add_member(request.user.username)
        return HttpResponseRedirect(reverse("profile", kwargs={"pk": request.user.id}))
    return render(
        request,
        "hkis/teams.html",
        {
            "teams": Team.objects.exclude(points__isnull=True)
            .order_by("-points")
            .select_related()
        },
    )


def team_view(request, slug):
    try:
        team = Team.objects.get(slug=slug)
    except Team.DoesNotExist:
        try:
            team = Team.objects.get(name=slug)
        except Team.DoesNotExist as err:
            raise Http404("Team does not exist") from err
        else:
            return redirect("team", slug=team.slug)
    requester_membership = None
    if not request.user.is_anonymous:
        with suppress(Membership.DoesNotExist):
            requester_membership = Membership.objects.get(team=team, user=request.user)
    context = {"team": team, "requester_membership": requester_membership}
    return render(request, "hkis/team.html", context)

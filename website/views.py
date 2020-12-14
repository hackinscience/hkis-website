from collections import OrderedDict
from contextlib import suppress
from itertools import groupby

from django.contrib.auth.models import Group
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.db.models import Count, Q, Max
from django.shortcuts import render
from django.utils.translation import gettext
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView
from django.views.generic.list import ListView
from website.models import Exercise, Answer, User, Team, Membership
from website.forms import AnswerForm


def index(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("exercises"))
    return render(request, "hkis/index.html")


def about(request):
    return render(request, "hkis/about.html")


def sponsor(request):
    return render(request, "hkis/sponsor.html")


def helppage(request):
    return render(request, "hkis/help.html")


def page_team(request):
    return render(request, "hkis/page_team.html")


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

    def dispatch(self, request, pk, *args, **kwargs):
        if pk != request.user.pk:
            raise PermissionDenied
        return super().dispatch(request, *args, pk=pk, **kwargs)

    def get_success_url(self):
        messages.info(self.request, "Profile updated")
        return reverse("profile", kwargs={"pk": self.request.user.id})


def leaderboard_view(request):
    context = {
        "players": enumerate(User.objects.order_by("-points")[:100], start=1),
    }
    return render(request, "hkis/leaderboard.html", context)


class ExerciseListView(ListView):
    model = Exercise
    template_name = "hkis/exercises.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(is_published=True)
            .with_global_stats()
            .with_user_stats(self.request.user)
            .select_related("category")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["by_category"] = [
            (key, list(values))
            for key, values in groupby(
                self.object_list, key=lambda exercise: exercise.category
            )
        ]
        return context


class ExerciseView(DetailView):
    model = Exercise
    template_name = "hkis/exercise.html"

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
        if user.is_anonymous:
            context["current_rank"] = 999999
        else:
            context["current_rank"] = self.request.user.rank
        if user.is_anonymous:
            context["is_valid"] = False
        else:
            context["is_valid"] = bool(
                self.object.answers.filter(user=user, is_valid=True)
            )
        context["solutions_qty"] = len(
            Answer.objects.filter(
                exercise__pk=self.object.id, is_valid=True, is_shared=True
            )
        )

        try:
            context["next"] = (
                Exercise.objects.filter(position__gt=self.object.position)
                .filter(is_published=True)
                .order_by("position")[0]
                .slug
            )
        except IndexError:
            context["next"] = None
        try:
            context["previous"] = (
                Exercise.objects.filter(position__lt=self.object.position)
                .order_by("-position")[0]
                .slug
            )
        except IndexError:
            context["previous"] = None
        return context


class SolutionView(LoginRequiredMixin, DetailView):
    model = Exercise
    template_name = "hkis/solutions.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["my_answers"] = Answer.objects.filter(
            exercise_id=self.object.id, user=self.request.user
        ).order_by("-created_at")
        context["solutions"] = []
        context["is_allowed_to_see_solutions"] = False
        already_seen = set()
        if self.object.answers.filter(user=self.request.user, is_valid=True):
            context["is_allowed_to_see_solutions"] = True
            for solution in Answer.objects.filter(
                exercise__pk=self.object.id, is_valid=True, is_shared=True
            ).order_by("created_at"):
                if solution.source_code not in already_seen:
                    context["solutions"].append(solution)
                    already_seen.add(solution.source_code)
        try:
            context["next"] = (
                Exercise.objects.filter(position__gt=self.object.position)
                .order_by("position")[0]
                .slug
            )
        except IndexError:
            context["next"] = None
        return context


def team_stats(request, team):
    try:
        team = Team.objects.get(name=team)
    except Team.DoesNotExist:
        raise Http404("Team does not exist")

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


def teams(request):
    if request.method == "POST":
        if request.POST.get("remove_from_team"):
            team = Team.objects.get(name=request.POST["remove_from_team"])
            if team.is_staff(request.user):
                team.remove_member(request.POST["member"])
            return HttpResponseRedirect(reverse("team", kwargs={"team": team.name}))
        if request.POST.get("accept_in_team"):
            team = Team.objects.get(name=request.POST["accept_in_team"])
            if team.is_staff(request.user):
                team.accept(request.POST["member"])
            return HttpResponseRedirect(reverse("team", kwargs={"team": team.name}))
        if request.POST.get("leave_team"):
            team = Team.objects.get(name=request.POST["leave_team"])
            team.remove_member(request.user.username)
        if request.POST.get("join_team"):
            team, _ = Team.objects.get_or_create(name=request.POST["join_team"])
            team.add_member(request.user.username)
        return HttpResponseRedirect(reverse("profile", kwargs={"pk": request.user.id}))
    if request.method == "GET":
        return render(
            request, "hkis/teams.html", {"teams": Team.objects.select_related()}
        )


def team(request, team):
    try:
        team = Team.objects.get(name=team)
    except Team.DoesNotExist:
        raise Http404("Team does not exist")
    requester_membership = None
    if not request.user.is_anonymous:
        with suppress(Membership.DoesNotExist):
            requester_membership = Membership.objects.get(team=team, user=request.user)
    context = {"team": team, "requester_membership": requester_membership}
    return render(request, "hkis/team.html", context)

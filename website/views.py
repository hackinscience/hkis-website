from collections import OrderedDict

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.db.models import Count, Q, Max
from django.shortcuts import render
from django.utils.translation import gettext
from django.contrib.auth.models import User
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView
from django.views.generic.list import ListView
from website.models import Exercise, Answer
from website.forms import AnswerForm


def index(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("exercises"))
    return render(request, "hkis/index.html")


def about(request):
    return render(request, "hkis/about.html")


def helppage(request):
    return render(request, "hkis/help.html")


def team(request):
    return render(request, "hkis/team.html")


def privacy(request):
    return render(request, "hkis/privacy.html")


@login_required
def dashboard_view(request):
    return render(request, "hkis/dashboard.html")


class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ["username", "email"]
    template_name = "hkis/profile_update.html"

    def get_success_url(self):
        messages.info(self.request, "Profile updated")
        return reverse("profile", kwargs={"pk": self.request.user.id})


class ExerciseListView(LoginRequiredMixin, ListView):
    model = Exercise
    template_name = "hkis/exercises.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(is_published=True)
            .with_global_stats()
            .with_user_stats(self.request.user)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        def _get_lead(wording):
            found = False
            for line in wording.split("\n"):
                if line.startswith("##"):
                    found = True
                    continue
                if line and found:
                    return line
            return ""

        context["exercises"] = [
            {
                **vars(exercise),
                "number": i + 1,
                "lead": _get_lead(exercise.wording),
                "tried": exercise.user_tries > 0,
                "done": exercise.user_successes > 0,
                "pct_tried": 100 * exercise.successes / (exercise.tries + 1),
            }
            for i, exercise in enumerate(self.object_list)
        ]
        return context


class ExerciseView(LoginRequiredMixin, DetailView):
    model = Exercise
    template_name = "hkis/exercise.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["LANGUAGE_CODE"] = self.request.LANGUAGE_CODE
        context["answers"] = answers = self.object.answers.filter(
            user=self.request.user
        ).order_by("-id")
        context["answer_form"] = AnswerForm(
            initial={
                "exercise": "/api/exercises/{}/".format(self.object.id),
                "source_code": answers[0].source_code
                if answers
                else context["exercise"].initial_solution,
            }
        )
        context["solutions"] = []
        context["object"].wording = gettext(context["object"].wording)
        if any(answer.is_valid for answer in answers):
            context["solutions"] = Answer.objects.filter(
                exercise__pk=self.object.id, is_valid=True, is_shared=True
            ).order_by("-created_at")
        try:
            context["next"] = (
                Exercise.objects.filter(position__gt=self.object.position)
                .order_by("position")[0]
                .slug
            )
        except IndexError:
            context["next"] = None
        return context


class StatsListView(UserPassesTestMixin, ListView):
    template_name = "hkis/stats_list.html"
    model = Group

    def get_queryset(self):
        self.queryset = self.request.user.groups.all()
        return super().get_queryset()

    def test_func(self):
        return self.request.user.has_perm("website.view_answer")


class StatsDetailView(UserPassesTestMixin, DetailView):
    template_name = "hkis/stats_detail.html"
    model = Group

    def test_func(self):
        return (
            self.request.user.has_perm("website.view_answer")
            and self.get_object() in self.request.user.groups.all()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats"] = OrderedDict(
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
                for user in User.objects.filter(groups=context["object"])
                .exclude(groups__name="prof")
                .order_by("username")
            ]
        )
        return context

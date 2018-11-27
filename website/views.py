from itertools import groupby

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse
from django.db import connection
from django.http import HttpResponse
from django.db.models import Count, Q
from django.shortcuts import render
from django.contrib.auth.models import User
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from website.models import Exercise, Answer
from website.forms import AnswerForm


def index(request):
    return render(request, "hkis/index.html")


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        def _get_lead(wording):
            try:
                return [line for line in wording.split("\n") if "Introduces" in line][0]
            except IndexError:
                return ""

        context["exercises"] = [
            {
                "id": exercise.id,
                "title": exercise.title,
                "lead": _get_lead(exercise.wording),
                "done": bool(
                    exercise.answers.filter(is_valid=True, user=self.request.user)
                ),
            }
            for exercise in self.object_list
        ]
        return context


class ExerciseView(LoginRequiredMixin, DetailView):
    model = Exercise
    template_name = "hkis/exercise.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["answers"] = self.object.answers.filter(
            user=self.request.user
        ).order_by("-id")
        try:
            context["answer_form"] = AnswerForm(
                initial={
                    "exercise": "/api/exercises/{}/".format(self.object.id),
                    "source_code": context["answers"][0].source_code,
                }
            )
        except IndexError:
            context["answer_form"] = AnswerForm(initial={"exercise": self.object.id})
        try:
            context["next_id"] = (
                Exercise.objects.filter(id__gt=self.object.id).order_by("id")[0].id
            )
        except IndexError:
            context["next_id"] = None
        return context


class AnswerCreateView(LoginRequiredMixin, CreateView):
    model = Answer
    form_class = AnswerForm
    template_name = "hkis/answer_form.html"

    def form_valid(self, form):
        form.cleaned_data["user"] = self.request.user
        super().form_valid(form)
        return HttpResponse("OK")


class StatsListView(UserPassesTestMixin, ListView):
    template_name = "hkis/stats_list.html"
    model = Group

    def test_func(self):
        return self.request.user.is_superuser


class StatsDetailView(UserPassesTestMixin, DetailView):
    template_name = "hkis/stats_detail.html"
    model = Group

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats"] = {
            user.username: [
                {"is_valid": exercice.nb_valid_anwser > 0, "exercice_id": exercice.id}
                for exercice in Exercise.objects.annotate(
                    nb_valid_anwser=Count(
                        "answers",
                        filter=Q(answers__is_valid=True) & Q(answers__user_id=user.id),
                    )
                ).all()
            ]
            for user in User.objects.filter(groups=context["object"])
        }
        return context

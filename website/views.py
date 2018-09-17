from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import render
from django.contrib.auth.models import User
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from website.models import Exercise, Answer
from website.forms import AnswerForm

def index(request):
    return render(request, 'hkis/index.html')

@login_required
def dashboard_view(request):
    return render(request, 'hkis/dashboard.html')

class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ['username', 'email']
    template_name = 'hkis/profile_update.html'

    def get_success_url(self):
        messages.info(self.request, "Profile updated")
        return reverse('profile', kwargs={'pk': self.request.user.id})

class ExerciseListView(LoginRequiredMixin, ListView):
    model = Exercise
    template_name = 'hkis/exercises.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        def _get_lead(wording):
            try:
                return [line for line in wording.split("\n") if 'Introduces' in line][0]
            except IndexError:
                return ""
        context['exercises'] = [{'id': exercise.id,
                                 'title': exercise.title,
                                 'lead': _get_lead(exercise.wording),
                                 'done': bool(exercise.answers.filter(is_valid=True, user=self.request.user))}
                                for exercise in self.object_list]
        return context

class ExerciseView(LoginRequiredMixin, DetailView):
    model = Exercise
    template_name = 'hkis/exercise.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['answers'] = self.object.answers.filter(user=self.request.user).order_by("-id")
        try:
            print(context['answers'][0])
            context['answer_form'] = AnswerForm(initial={
                'exercise': self.object.id,
                'source_code': context['answers'][0].source_code})
        except IndexError:
            context['answer_form'] = AnswerForm(initial={
                'exercise': self.object.id})
        return context


class AnswerCreateView(LoginRequiredMixin, CreateView):
    model = Answer
    form_class = AnswerForm
    template_name = 'hkis/answer_form.html'

    def form_valid(self, form):
        form.cleaned_data['user'] = self.request.user
        return super().form_valid(form)

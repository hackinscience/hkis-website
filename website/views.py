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

class ProfileView(UpdateView, LoginRequiredMixin):
    model = User
    fields = ['username', 'email']
    template_name = 'hkis/profile_update.html'

    def get_success_url(self):
        messages.info(self.request, "Profile updated")
        return reverse('profile', kwargs={'pk': self.request.user.id})

class ExerciseListView(ListView, LoginRequiredMixin):
    model = Exercise
    template_name = 'hkis/exercises.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['done'] = []
        context['todo'] = []
        for obj in self.object_list:
            if obj.answers.filter(is_valid=True):
                context['done'].append(obj)
            else:
                context['todo'].append(obj)
        return context

class ExerciseView(DetailView, LoginRequiredMixin):
    model = Exercise
    template_name = 'hkis/exercise.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['answers'] = self.object.answers.all().order_by("-id")
        context['answer_form'] = AnswerForm(initial={'exercise': self.object.id})
        return context


class AnswerCreateView(CreateView):
    model = Answer
    form_class = AnswerForm
    template_name = 'hkis/answer_form.html'

    def form_valid(self, form):
        form.cleaned_data['user'] = self.request.user
        return super().form_valid(form)

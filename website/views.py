from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
#from django.http import HttpResponse
#from django.template import loader
from django.urls import reverse
from django.shortcuts import render
from django.contrib.auth.models import User
from django.views.generic.edit import UpdateView
from django.views.generic.list import ListView
from website.models import Exercise

def index(request):
    return render(request, 'hkis/index.html')

@login_required
def dashboard_view(request):
    return render(request, 'hkis/dashboard.html')

class UpdateProfile(UpdateView, LoginRequiredMixin):
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

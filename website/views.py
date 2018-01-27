from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.template import loader
from django.urls import reverse
from django.shortcuts import render
from django.contrib.auth.models import User
from django.views.generic.edit import UpdateView

@login_required
def dashboard_view(request):
    template = loader.get_template('hkis/dashboard.html')
    return render(request, 'hkis/dashboard.html')


class UpdateProfile(UpdateView):
    model = User
    fields = ['username', 'email']
    template_name = 'hkis/profile_update.html'

    def get_success_url(self):
        messages.info(self.request, "Profile updated")
        return reverse('profile', kwargs={'pk': self.request.user.id})

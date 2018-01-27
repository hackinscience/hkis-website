from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render

@login_required
def dashboard_view(request):
    template = loader.get_template('hkis/dashboard.html')
    return render(request, 'hkis/dashboard.html')

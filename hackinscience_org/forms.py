from django import forms
from django.utils.translation import gettext_lazy
from registration.forms import RegistrationForm


class HkisRegistrationForm(RegistrationForm):
    email = forms.EmailField(label=gettext_lazy("E-mail (optional)"), required=False)
    field_order = ["username", "password1", "password2", "email"]

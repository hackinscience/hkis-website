from django import forms
from django.utils.translation import ugettext_lazy as _
from django_ace import AceWidget
from registration.forms import RegistrationForm
from website.models import Answer


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ["source_code", "exercise"]
        widgets = {
            "source_code": AceWidget(
                mode="python",
                theme="twilight",
                width="100%",
                height="70vh",
                fontsize="16px",
                toolbar=False,
                showgutter=False,
                behaviours=False,
            ),
            "exercise": forms.HiddenInput(),
        }


class HkisRegistrationForm(RegistrationForm):
    email = forms.EmailField(label=_("E-mail (optional)"), required=False)
    field_order = ["username", "password1", "password2", "email"]

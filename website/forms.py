from django import forms
from django_ace import AceWidget
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
                height="400px",
                fontsize="16px",
            ),
            "exercise": forms.HiddenInput(),
        }

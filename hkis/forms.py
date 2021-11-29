from django import forms
from django_ace import AceWidget
from hkis.models import Answer


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ["source_code", "exercise"]
        widgets = {
            "source_code": AceWidget(
                mode="python",
                theme="twilight",
                width="100%",
                height="100%",
                fontsize="16px",
                toolbar=False,
                showgutter=True,
                behaviours=False,
            ),
            "exercise": forms.HiddenInput(),
        }

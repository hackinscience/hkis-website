from django import forms
from django_ace import AceWidget
from website.models import Answer


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ["source_code", "exercise"]
        widgets = {
            "source_code": AceWidget(
                mode="python", theme="twilight", width="600px", height="400px"
            ),
            "exercise": forms.HiddenInput(),
        }

    def save(self, commit=True):
        instance = super(AnswerForm, self).save(commit=False)
        instance.user = self.cleaned_data["user"]
        if commit:
            instance.save()
        return instance

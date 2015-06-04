from django import forms

class WorkerForm(forms.Form):
    answer = forms.NullBooleanField(label='answer')
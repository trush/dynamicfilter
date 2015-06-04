from django import forms
from models import RestaurantPredicate

class WorkerForm(forms.Form):
    answer = forms.NullBooleanField(label='answer')
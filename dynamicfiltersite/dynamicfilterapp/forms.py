from django import forms
from models import RestaurantPredicate

class WorkerForm(forms.Form):
    answer = forms.NullBooleanField(label='Your answer')

class IDForm(forms.Form):
    workerID = forms.CharField(label='Worker ID')
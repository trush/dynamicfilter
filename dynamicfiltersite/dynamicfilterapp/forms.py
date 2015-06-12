from django import forms
from models import Restaurant, RestaurantPredicate

class WorkerForm(forms.Form):

    #choice fields for worker answering predicates
    WORKER_ANSWER_CHOICES = (
        (None, "------"),
        (True, 'Yes'),
        (False, 'No'),
    )

    #how confident a worker is in his/her answer
    CONFIDENCE_LEVELS = (
        ('50', '50%'),
        ('60', '60%'),
        ('70', '70%'),
        ('80', '80%'),
        ('90', '90%'),
        ('100', '100%'),
    )

    #sets up form for answering predicate and worker's confidence level
    answerToQuestion = forms.ChoiceField(choices=WORKER_ANSWER_CHOICES, label='Your answer')
    confidenceLevel = forms.ChoiceField(choices=CONFIDENCE_LEVELS, label='Confidence level')

class RestaurantAdminForm(forms.ModelForm):

    class Meta:
        model = Restaurant
        fields = ['name', 'url', 'text', 'street']

    def save(self, commit=True):
        instance = super(RestaurantAdminForm, self).save(commit=False)
        if commit:
            instance.save()
        RestaurantPredicate.objects.create(restaurant=instance, question="Do they serve Austin Shin?")
        RestaurantPredicate.objects.create(restaurant=instance, question="Would you recommend the Kate Reed?")
        RestaurantPredicate.objects.create(restaurant=instance, question="Are you Prof Beth?")
        return instance

class IDForm(forms.Form):
    workerID = forms.IntegerField(label='Worker ID')

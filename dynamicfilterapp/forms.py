# -*- coding: utf-8 -*-
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import pre_save
from django import forms
from models import *

class WorkerForm(forms.Form):
    """
    Form for a crowd worker to enter a vote on an item-predicate pair.
    """
    WORKER_ANSWER_CHOICES = (
        (True, "Yes"),
        (False, "No"),
    )

    # Set up two fields for worker's answer and feedback
    answer = forms.ChoiceField(choices=WORKER_ANSWER_CHOICES, 
        widget=forms.Select(), label="Answer Choices:")
    feedback = forms.CharField(widget=forms.Textarea, 
        label='Comments/Concerns/Feedback:', required=False)

class IDForm(forms.ModelForm):
    """
    Form for worker to enter ID number before going to the "Answer a Question" 
    page. Not needed for experiments run on Mechanical Turk, since ID information 
    is recorded automatically there. (Mainly for site testing purposes.)
    Uses the WorkerID model to validate input as a positive integer.
    """
    class Meta:
        
        # Tells Django which model is being created and which fields to display
        model = WorkerID
        fields = ['workerID'] 
        
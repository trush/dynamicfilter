from django import forms
from django.db import models
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.core.urlresolvers import reverse
from django.db.models import F
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormView
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_exempt

from .models import *
from .forms import *
from views_helpers import *

@xframe_options_exempt
def workerForm(request):
    """
    Page the worker sees to complete the question
    """
    # if request.GET.get("assignmentId") == "ASSIGNMENT_ID_NOT_AVAILABLE": # worker has not accepted HIT yet
    #    return render(request,'externalhit/preview.html',{}) # render the fake page with empty context
    workerId = request.GET.get("workerId")
    assignmentId = request.GET.get("assignmentId")
    hitId = request.GET.get("hitId")
    print workerId
    # submitURL = request.GET.get("turkSubmitTo") + "/mturk/externalSubmit"
    # ip_pair = IP_Pair.objects.get(pk=1)
    # # ip_pair = pending_eddy(workerID, ip_pair) # update the ip_pair to display
    # context = { 'question' : ip_pair.predicate.question.question_text,
    #     'item' : ip_pair.item.name
    # #    'workerId' : workerId, 'assignmentId' : assignmentId, 'hitId' : hitId, 'url':submitURL }
    #     }
    context = {'question' : 'are you having a good day?', 
        'item': 'it is a Wednesday', 
        'workerId':workerId, 'assignmentId':assignmentId, 'hitId' : 3}
    return render(request, 'dynamicfilterapp/workerform.html', context)

def testfun(request):
    return HttpResponse("Hello, world. You're at the dynamicfilter app.")

@xframe_options_exempt
def vote(request):
    """
    Page that loads in all the data from the worker task and updates the dataset
    """
    #load in data from workerForm

    form_answer = int(request.POST.get("workervote"))
    print form_answer
    feedback = request.POST.get("feedback")
    print feedback
    # workerId = request.POST.get("workerId")
    # assignmentId = request.POST.get("assignmentId")
    # hitId = request.POST.get("hitId")
    # submitURL = request.POST.get("submitURL")
    # task = Task(ip_pair=questionedPair,
    #    answer=form_answer,
    #    workerID = workerId,
    #    feedback=feedback)
    #task.save()

    return render(request, 'dynamicfilterapp/interm_page.html')

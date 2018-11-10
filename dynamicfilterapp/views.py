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
from django.views.decorators.csrf import csrf_exempt

from .models import *
from .forms import *
from views_helpers import *
from data_load import *

@xframe_options_exempt
@csrf_exempt  #############DELETE AFTER TESTING
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
    #     'workerId' : workerId, 'assignmentId' : assignmentId, 'hitId' : hitId, 'url':submitURL }
    #     }
    context = {'question' : 'are you having a good day?', 
        'item': 'it is a Wednesday', 
        'workerId':workerId, 'assignmentId':assignmentId, 'hitId' : hitId}
    return render(request, 'dynamicfilterapp/workerform.html', context)

def testfun(request):
    return HttpResponse("Hello, world. You're at the dynamicfilter app.")

@xframe_options_exempt
@csrf_exempt ###########DELETE AFTER TESTING
def databaseTest(request):
    IP_Pair.objects.all().delete()
    Predicate.objects.all().delete()
    Question.objects.all().delete()
    Item.objects.all().delete()
    # q = Question(question_ID=1, question_text="Are you having a good day?")
    # q.save()
    # i1 = Item(item_ID=1, name="Wednesday", item_type=toggles.ITEM_TYPE)
    # i1.save()
    # p = Predicate(predicate_ID=1, question=q)
    # p.save()
    # ip1 = IP_Pair(item = i1, predicate = p)
    # ip1.save()
    # q1 = Question.objects.get(question_ID=1)
    # context = {'question' : q1, 
    #     'item': i1, 
    #     'workerId':4, 'assignmentId':3, 'hitId' : 2}

    load_database()
    
    # return render(request, 'dynamicfilterapp/workerform.html', context)
    return render(request, 'dynamicfilterapp/no_questions.html')

@xframe_options_exempt
@csrf_exempt ###########DELETE AFTER TESTING
def vote(request):
    """
    Page that loads in all the data from the worker task and updates the dataset
    """
    #load in data from workerForm

    form_answer = (request.POST.get("workervote"))
    print form_answer
    feedback = request.POST.get("feedback")
    print feedback
    workervote = form_answer
    workerId = request.POST.get("workerId")
    assignmentId = request.POST.get("assignmentId")
    hitId = request.POST.get("hitId")
    elapsed_time = request.POST.get("elapsed_time")
    # submitURL = request.POST.get("submitURL")
    # task = Task(ip_pair=questionedPair,
    #    answer=form_answer,
    #    workerID = workerId,
    #    feedback=feedback)
    #task.save()
    context = {'question' : 'are you having a good day?', 
        'workervote': workervote, 'elapsed_time': elapsed_time,
        'workerId':workerId, 'assignmentId':assignmentId, 'hitId' : hitId}

    return render(request, 'dynamicfilterapp/interm_page.html', context)


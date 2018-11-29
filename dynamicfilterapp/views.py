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
    if not workerId:
        workerId = -1
    assignmentId = request.GET.get("assignmentId")
    if not assignmentId:
        assignmentId = -1
    hitId = request.GET.get("hitId")
    if not hitId:
        hitId = -1
    ip_pair, eddy_time = give_task(None, workerId)
    if not ip_pair:
        question = "no question found"
        pred_id = -1
        item_id = -1
        item = "no item found"
    else:
        question = ip_pair.predicate.question.question_text
        pred_id = ip_pair.predicate.predicate_ID
        item_id = ip_pair.item.name
        item = ip_pair.item.name
    # submitURL = request.GET.get("turkSubmitTo") + "/mturk/externalSubmit"
    # ip_pair = IP_Pair.objects.get(pk=1)
    # # ip_pair = pending_eddy(workerID, ip_pair) # update the ip_pair to display
    # context = { 'question' : ip_pair.predicate.question.question_text,
    #     'item' : ip_pair.item.name
    #     'workerId' : workerId, 'assignmentId' : assignmentId, 'hitId' : hitId, 'url':submitURL }
    #     }
    context = {'question' : question, 
        'item': item, 
        'pred': pred_id, 'item_id': item_id,
        'workerId':workerId, 'assignmentId':assignmentId, 'hitId' : hitId}
    return render(request, 'dynamicfilterapp/workerform.html', context)

def testfun(request):
    return HttpResponse("Hello, world. You're at the dynamicfilter app.")

@xframe_options_exempt
@csrf_exempt ###########DELETE AFTER TESTING
def databaseReset(request):
    ''' 
    Deletes all objects and reloads the database. SHOULD NOT BE INCLUDED IN A LIVE VERSION.
    '''
    Task.objects.all().delete()
    DummyTask.objects.all().delete()
    IP_Pair.objects.all().delete()
    Predicate.objects.all().delete()
    Question.objects.all().delete()
    Item.objects.all().delete()

    load_database()
    # The render here is mostly just so the site has something to show.
    # This view only exists to make it convenient to refresh the database
    # on the deployed app during testing.
    return render(request, 'dynamicfilterapp/no_questions.html')

@xframe_options_exempt
@csrf_exempt ###########DELETE AFTER TESTING
def vote(request):
    """
    Page that loads in all the data from the worker task and updates the dataset
    """
    #load in data from workerForm
    workervote =  request.POST.get("workervote")
    feedback = request.POST.get("feedback")
    workerId = request.POST.get("workerId")
    assignmentId = request.POST.get("assignmentId")
    hitId = request.POST.get("hitId")
    elapsed_time = request.POST.get("elapsed_time")
    pred = request.POST.get("pred")
    item_id = request.POST.get("item_id")
    question = request.POST.get("question")

    # submitURL = request.POST.get("submitURL")

    #finds IP pair for which to record this vote
    qItem = Item.objects.get(item_id = item_id)
    qPred = Predicate.objects.get(predicate_ID=pred)
    questionedPair = IP_Pair.objects.get(item=qItem,predicate=qPred)

    #create a task for updating the database
    task = Task(ip_pair=questionedPair,
       answer=workervote,
       workerID = workerId,
       feedback=feedback)
    task.save()

    #update database with answer
    updateCounts(task, questionedPair)


    context = {'question' : question, 'pred': pred,
        'workervote': workervote, 'elapsed_time': elapsed_time,
        'workerId':workerId, 'assignmentId':assignmentId, 'hitId' : hitId}

    return render(request, 'dynamicfilterapp/interm_page.html', context)


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
import csv

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


    if not Predicate.objects.filter(queue_is_full = False):
        question = "question cannot be answered right now, please try again"
        pred_id = -1
        item_id = -1
        item = "please try again"
        context = {'question' : question, 
            'item': item, 
            'pred': pred_id, 'item_id': item_id,
            'workerId':workerId, 'assignmentId':assignmentId, 'hitId' : hitId}
        return render(request, 'dynamicfilterapp/workerform.html', context)

    try:
        ip_pair, eddy_time = give_task(None, workerId)
    except:
        question = "error finding question, please retry"
        pred_id = -1
        item_id = -1
        item = "error finding item, please try again"
        context = {'question' : question, 
            'item': item, 
            'pred': pred_id, 'item_id': item_id,
            'workerId':workerId, 'assignmentId':assignmentId, 'hitId' : hitId}
        return render(request, 'dynamicfilterapp/workerform.html', context)


    if ip_pair:
        question = ip_pair.predicate.question.question_text
        pred_id = ip_pair.predicate.predicate_ID
        item_id = ip_pair.item.item_ID
        item = ip_pair.item.name
    else:
        question = "no question found"
        pred_id = -1
        item_id = -1
        item = "no item found"

    # old error-checking code, may still be necessary
    # if Item.objects.filter(isDone = False):
    #     ip_pair, eddy_time = give_task(None, workerId)
    #     if not ip_pair:
    #         question = "ip pair missing, please try again"
    #         pred_id = -1
    #         item_id = -1
    #         item = "placeholder"
    #     else:
    #         question = ip_pair.predicate.question.question_text
    #         pred_id = ip_pair.predicate.predicate_ID
    #         item_id = ip_pair.item.item_ID
    #         item = ip_pair.item.name
    # else:
    #     question = "no question found"
    #     pred_id = -1
    #     item_id = -1
    #     item = "no item found"

    


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

    # submitURL = request.POST.get("submitURL")

    #finds IP pair for which to record this vote
    qItem = Item.objects.get(item_ID = item_id)
    if not qItem:
        raise Exception("no item found for id: " + str(item_id))
    qPred = Predicate.objects.get(predicate_ID=pred)
    if not qPred:
        raise Exception("no pred found for id: " + str(pred))
    questionedPair = IP_Pair.objects.get(item=qItem,predicate=qPred)
    if not questionedPair:
        raise Exception("no ip pair found for item: " + str(item_id) + "and pred: " + str(pred))

    question = qPred.question.question_text

    #create a task for updating the database
    task = Task(ip_pair=questionedPair,
       answer=workervote,
       workerID = workerId,
       start_time = 0,
       end_time = elapsed_time,
       feedback=feedback)
    task.save()

    #update database with answer
    
    updateCounts(task, questionedPair)

    #delete task to save db space. This means data tracking has to happen in real time on the site.
    task.delete()


    context = {'question' : question, 'pred': pred,
        'workervote': workervote, 'elapsed_time': elapsed_time,
        'workerId':workerId, 'assignmentId':assignmentId, 'hitId' : hitId}

    return render(request, 'dynamicfilterapp/interm_page.html', context)

@xframe_options_exempt
@csrf_exempt ###########DELETE AFTER TESTING
def display(request):
    '''
    Displays information about IP pairs' completeness and probably more later.
    '''
    # ipstring = "Completed IP pairs: \n"

    completedIP = IP_Pair.objects.filter(isDone=False)
    if not completedIP:
        return HttpResponse("No completed IP pairs.")
    else:
        context = {'iplist': completedIP}
        # for ip in completedIP:
        #     ipstring += "- " + ip.item.name + "/" + ip.predicate.question.question_text + "\n"

    return render(request, 'dynamicfilterapp/disp.html', context)


@xframe_options_exempt
@csrf_exempt ###########DELETE AFTER TESTING
def getTix(request):
    '''
    Finds current tickets for each predicate
    '''
    preds = Predicate.objects.all()
    if not preds:
        return HttpResponse("No preds.")
    else:
        context = {'preds': preds}

    return render(request, 'dynamicfilterapp/tickets.html', context)


@xframe_options_exempt
@csrf_exempt ###########DELETE AFTER TESTING
def summary(request):
    preds = Predicate.objects.all().order_by("predicate_ID")
    if not preds or not (Item.objects.all()):
        return HttpResponse("Database not loaded.")

    passedItems = Item.objects.filter(hasFailed = False)
    failedItems = Item.objects.filter(hasFailed = True)
    numPassed = len(passedItems)
    numFailed = len(failedItems)
    numItems = len(Item.objects.all())

    context = {'preds':preds, 'passedItems':passedItems, 
        'failedItems':failedItems, 'numPassed':numPassed,
        'numFailed':numFailed, 'numItems':numItems}

    return render(request, 'dynamicfilterapp/summary.html', context)
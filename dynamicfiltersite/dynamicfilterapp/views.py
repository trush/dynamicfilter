from django import forms
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.db import models

from .models import Restaurant, RestaurantPredicate, Task, PredicateBranch
from .forms import WorkerForm, IDForm
from views_helpers import *

from scipy.special import btdtr
import random

def index(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = IDForm(request.POST)
        
        # check whether it's valid:
        if form.is_valid():
            IDnumber = form.cleaned_data['workerID']
            
            # redirect to a new URL:
            return HttpResponseRedirect('/dynamicfilterapp/answer_question/id=' + str(IDnumber))

    # if a GET (or any other method) we'll create a blank form
    else:
        form = IDForm()

    return render(request, 'dynamicfilterapp/index.html', {'form': form})

def answer_question(request, IDnumber):
    """
    Displays and processes input from a form where the user can answer a question about a
    predicate.
    """
    # if this is a POST request we need to process the form data
    if request.method == 'POST':

        # create a form instance and populate it with data from the request:
        form = WorkerForm(request.POST, label_suffix='')
        toBeAnswered = RestaurantPredicate.objects.filter(id=request.POST.get('pred_id'))[0]
        print toBeAnswered
        # check whether it's valid:
        if form.is_valid():

            # get time to complete in number of milliseconds, or use flag value if there's no elapsed_time
            timeToComplete = request.POST.get('elapsed_time', 42)

            # Convert entered answer to type compatible with NullBooleanField
            form_answer = None
            idk = False

            print form.cleaned_data
            # if worker answered Yes
            if float(form.cleaned_data['answerToQuestion']) > 0:
                form_answer = True

            # if worker answered No
            elif float(form.cleaned_data['answerToQuestion']) < 0:
                form_answer = False

            elif float(form.cleaned_data['answerToQuestion']) == 0:
                idk = True

            confLevel = abs(float(form.cleaned_data['answerToQuestion'])*100)

            # create a new Task with relevant information and store it in the database
            task = Task(restaurantPredicate = toBeAnswered, answer = form_answer, confidenceLevel=confLevel,
                workerID = IDnumber, completionTime = timeToComplete, IDontKnow=idk, feedback=form.cleaned_data['feedback'])
            task.save()

             # get the PredicateBranch associated with this predicate
            pB = PredicateBranch.objects.filter(question=toBeAnswered.question)[0]
            updateCounts(pB, task)

            # decreases status of one predicate in the restaurant by 1 because it was just answered
            decrementStatus(toBeAnswered.index, toBeAnswered.restaurant)

            statusName = "predicate" + str(toBeAnswered.index) + "Status"
            if getattr(toBeAnswered.restaurant, statusName)==0:
                # then aggregate responses to check if the predicate has been answered enough times to have a fixed value
                toBeAnswered.restaurant = aggregate_responses(toBeAnswered)     

            # now the toBeAnswered restaurant comes out of the predicate branch and is not being evaluated anymore 
            toBeAnswered.restaurant.evaluator = None

            # set the queue index to be right after the current last thing (only used in eddy 2)
            currentLastIndex = Restaurant.objects.order_by('-queueIndex')[0].queueIndex
            toBeAnswered.restaurant.queueIndex = currentLastIndex + 1
            
            toBeAnswered.save()

            # redirect to a new URL:
            return HttpResponseRedirect('/dynamicfilterapp/completed_question/id=' + IDnumber)

    # if a GET (or any other method) we'll create a blank form
    else:
        toBeAnswered = eddy2(IDnumber)
        print "toBeAnswered: " + str(toBeAnswered)
        # if there are no predicates to be answered by the worker with this ID number
        if toBeAnswered == None:
            return HttpResponseRedirect('/dynamicfilterapp/no_questions/id=' + IDnumber)
        form = WorkerForm(label_suffix='')

    return render(request, 'dynamicfilterapp/answer_question.html', {'form': form, 'predicate': toBeAnswered, 'workerID': IDnumber })

def completed_question(request, IDnumber):
    """
    Displays a page informing the worker that their answer was recorded, with a link to
    answer another question.
    """
    return render(request, 'dynamicfilterapp/completed_question.html', {'workerID': IDnumber})

def no_questions(request, IDnumber):
    """
    Displays a page informing the worker that no questions need answering by them.
    """
    return render(request, 'dynamicfilterapp/no_questions.html', {'workerID': IDnumber})

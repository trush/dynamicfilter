from django.shortcuts import render
from django.http import HttpResponse
from models import Restaurant, RestaurantPredicate, Task
from django.db import models

def index(request):
	return render(request, 'dynamicfilterapp/index.html')

def answer_question(request):
	context = {}

	# get all the RestaurantPredicates in the database
	restaurantPredicates = RestaurantPredicate.objects.all()

	# if there aren't any RestaurantPredicates, set error message for template and return
	if not restaurantPredicates.exists():
		context['errorMessage'] = "There are no existing predicates."
		return render(request, 'dynamicfilterapp/answer_question.html', context)

	# find the first unanswered predicate if it exists
	toBeAnswered = None
	assert restaurantPredicates.exists()
	for predicate in restaurantPredicates:
		if predicate.value == None:
	 		toBeAnswered = predicate
	 		break
	
	# if there was no unanswered predicate, set error message for template and return
	if toBeAnswered == None:
		context['errorMessage'] = "There are no unanswered predicates."
		return render(request, 'dynamicfilterapp/answer_question.html', context)

	# if there was an unanswered predicate, put information needed to 
	# render template in context dictionary
	context['restaurantName'] = toBeAnswered.restaurant.name
	context['restaurantText'] = toBeAnswered.restaurant.text
	context['questionText'] = toBeAnswered.question

	return render(request, 'dynamicfilterapp/answer_question.html', context)

def completed_question(request):
	return HttpResponse("You answered a question!")

def enter_task(request):
	# make a new task object using the worker-entered data and save it
	# to the database
	return HttpResponse("Enter-a-task view")




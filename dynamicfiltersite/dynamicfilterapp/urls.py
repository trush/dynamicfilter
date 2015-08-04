from django.conf.urls import url
from . import views

# the worker ID is passed between views as a URL parameter
urlpatterns = [
	url(r'^$', views.index, name='index'),
    url(r'^answer_question/id=([0-9]+)/$', views.answer_question, name='answer_question'),
    url(r'^completed_question/id=([0-9]+)/$', views.completed_question, name='completed_question'),
    url(r'^no_questions/id=([0-9]+)/$', views.no_questions, name='no_questions'),
]
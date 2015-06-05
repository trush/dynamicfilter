from django.conf.urls import url

from . import views

urlpatterns = [
	url(r'^$', views.index, name='index'),
    url(r'^answer_question/id=([0-9]{3})/$', views.answer_question, name='answer_question'),
    url(r'^completed_question/id=([0-9]{3})/$', views.completed_question, name='completed_question'),
    url(r'^enter_task', views.completed_question, name='enter_task'),
]
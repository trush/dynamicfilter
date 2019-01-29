from django.conf.urls import url
from . import views

# the worker ID is passed between views as a URL parameter
urlpatterns = [
	url(r'^$', views.workerForm, name='worker_form'),
	url(r'^vote', views.vote, name='vote'),
	url('fun', views.testfun, name='funtest'),
	url('dbr', views.databaseReset, name='tester'),
	url('display', views.display, name='info'),
	url('displayt', views.displayCSV, name='taskinfo')
]
from django.conf.urls import url
from . import views

# the worker ID is passed between views as a URL parameter
urlpatterns = [
	url(r'^$', views.workerForm, name='worker_form'),
	url(r'^vote', views.vote, name='vote'),
	url('fun', views.testfun, name='funtest')
]
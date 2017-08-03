from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^report', views.report),
    url(r'^information', views.info),
]

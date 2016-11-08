from django.conf.urls import url
from . import views

urlpatterns = [
        url(r'$', views.disease_query, name='disease_query'),
        url(r'results/$', views.article_query, name='article_query'),
]

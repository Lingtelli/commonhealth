from django.conf.urls import url
from . import views

urlpatterns = [
        url(r'v1/', views.disease_query, name='disease_query'),
        url(r'v2/$', views.article_query, name='article_query'),
]

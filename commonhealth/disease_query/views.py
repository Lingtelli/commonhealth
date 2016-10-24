from django.shortcuts import render, get_object_or_404
from django.template import loader
from django.http import HttpResponse


# Create your views here.
def disease_query(request):
    return render(request, 'disease_query/disease_query.html')

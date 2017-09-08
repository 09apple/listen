from django.http import HttpResponse
from django.shortcuts import render

def index(request):
    return render(request, 'listener/index.html', context={
        'title': 'lll',
        'welcome': 'wwwwww'
                    })
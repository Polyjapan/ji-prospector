from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponse

# Create your views here
def index(request):
    if request.user.is_authenticated:
        return HttpResponse('<p>Welcome.</p><p>You logged in as <strong>{}</strong>.</p><p><a href="{}">Logout</a></p>'.format(request.user.get_full_name(), reverse('users:cas_ng_logout')))
    else:
        return HttpResponse('<p>Welcome.</p><p><a href="{}">Login</a></p>'.format(reverse('users:cas_ng_login')))

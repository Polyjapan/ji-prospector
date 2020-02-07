"""prospector URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

import prospector.views as views

app_name = 'polls'
urlpatterns = [
    path('', views.index, name='index'),
    path('plan', views.plan, name='plan'),
    path('contacts', views.contacts_list, name='contacts.list'),
    path('contacts/<int:pk>', views.contacts_show, name='contacts.show'),
    path('deals', views.deals_list, name='deals.list'),
    path('deals/<int:pk>', views.deals_show, name='deals.show'),
]

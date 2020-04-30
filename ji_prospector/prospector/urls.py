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

app_name = 'prospector'
urlpatterns = [
    path('', views.index, name='index'),
    path('quickstart', views.quickstart, name='quickstart'),
    path('plan', views.plan, name='plan'),

    path('contacts', views.contacts_list, name='contacts.list'),
    path('contacts/<int:pk>', views.contacts_show, name='contacts.show'),

    path('deals', views.deals_list, name='deals.list'),
    path('deals/<int:pk>', views.deals_show, name='deals.show'),

    path('tasktypes', views.tasktypes_list, name='tasktypes.list'),
    path('tasktypes/<int:pk>', views.tasktypes_show, name='tasktypes.show'),

    path('tasks', views.tasks_list, name='tasks.list'),
    path('tasks/history/<int:pk>', views.tasks_history, name='tasks.history'),
    path('tasks/comments/<int:pk>', views.tasks_comments, name='tasks.comments'),
    path('tasks/comments/delete/<int:pk>', views.tasks_delete_comment, name='tasks.delete_comment'),
    path('tasks/settodostate/pk=<int:pk>/state=<str:state>', views.tasks_set_todostate, name='tasks.set_todostate'),
    path('tasks/logtodostate/pk=<int:pk>', views.tasks_log_todostate, name='tasks.log_todostate'),
    path('tasks/embed', views.tasks_list_embed, name='tasks.list_embed'),
    path('tasks/embed/tasktype=<int:fixed_tasktype>', views.tasks_list_embed, name='tasks.list_embed_fixed_tasktype'),
    path('tasks/embed/deal=<int:fixed_deal>', views.tasks_list_embed, name='tasks.list_embed_fixed_deal'),
    path('tasks/embed/tasktype=<int:fixed_tasktype>/deal=<int:fixed_deal>', views.tasks_list_embed, name='tasks.list_embed_fixed_both'),

    path('events', views.events_list, name='events.list'),
    path('events/<int:pk>', views.events_show, name='events.show'),

]

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
from prospector.models import *

app_name = 'prospector'
urlpatterns = [
    path('', views.index, name='index'),
    path('quickstart', views.quickstart, name='quickstart'),
    path('plan', views.plan, name='plan'),

    path('contacts', views.list_view(Contact, 'contacts'), name='contacts.list'),
    path('contacts/archive', views.list_view(Contact, 'contacts', archive=True), name='contacts.archive'),
    path('contacts/create', views.contacts_edit, {'create': True}, name='contacts.create'),
    path('contacts/<int:pk>', views.contacts_show, name='contacts.show'),
    path('contacts/<int:pk>/edit', views.contacts_edit, name='contacts.edit'),
    path('contacts/<int:pk>/delete', views.delete_view(Contact, 'contacts'), name='contacts.delete'),
    path('contacts/<int:pk>/undelete', views.undelete_view(Contact, 'contacts'), name='contacts.undelete'),

    path('deals', views.list_view(Deal, 'deals'), name='deals.list'),
    path('deals/archive', views.list_view(Deal, 'deals', archive=True), name='deals.archive'),
    path('deals/create', views.deals_edit, {'create': True}, name='deals.create'),
    path('deals/<int:pk>', views.deals_show, name='deals.show'),
    path('deals/<int:pk>/edit', views.deals_edit, name='deals.edit'),
    path('deals/<int:pk>/explaintags', views.deals_explaintags, name='deals.explaintags'),
    path('deals/<int:pk>/defaulttasks', views.deals_defaulttasks, name='deals.defaulttasks'),
    path('deals/<int:pk>/delete', views.delete_view(Deal, 'deals'), name='deals.delete'),
    path('deals/<int:pk>/undelete', views.undelete_view(Deal, 'deals'), name='deals.undelete'),

    path('tasktypes', views.tasktypes_list, name='tasktypes.list'),
    path('tasktypes/archive', views.list_view(TaskType, 'tasktypes', archive=True), name='tasktypes.archive'),
    path('tasktypes/create', views.tasktypes_edit, {'create': True}, name='tasktypes.create'),
    path('tasktypes/<int:pk>', views.tasktypes_show, name='tasktypes.show'),
    path('tasktypes/<int:pk>/edit', views.tasktypes_edit, name='tasktypes.edit'),
    path('tasktypes/<int:pk>/delete', views.delete_view(TaskType, 'tasktypes'), name='tasktypes.delete'),
    path('tasktypes/<int:pk>/undelete', views.undelete_view(TaskType, 'tasktypes'), name='tasktypes.undelete'),

    path('tasks', views.tasks_list, name='tasks.list'),
    path('tasks/<int:pk>/delete', views.delete_view(Task, 'tasks'), name='tasks.delete'),
    path('tasks/<int:pk>/history', views.tasks_history, name='tasks.history'),
    path('tasks/<int:pk>/comments/', views.tasks_comments, name='tasks.comments'),
    path('tasks/comments/<int:pk>/delete', views.tasks_delete_comment, name='tasks.delete_comment'),
    path('tasks/<int:pk>/settodostate', views.tasks_set_todostate, name='tasks.set_todostate'),
    path('tasks/<int:pk>/logtodostate', views.tasks_log_todostate, name='tasks.log_todostate'),
    path('tasks/embed', views.tasks_list_embed, name='tasks.list_embed'),

    path('events', views.events_list, name='events.list'),
    path('events/create', views.events_edit, {'create': True}, name='events.create'),
    path('events/<int:pk>', views.events_show, name='events.show'),
    
    path('fanzines/register', views.fanzine_register, name='fanzines.register'),
    path('fanzines', views.fanzine_list, name='fanzines.list'),
    path('fanzines/<int:pk>', views.fanzines_show, name='fanzines.show'),
    path('fanzines/delete', views.fanzines_delete, name='fanzines.delete'),
    path('fanzines/add', views.fanzines_add, name='fanzines.add'),

]

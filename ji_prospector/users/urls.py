from django.urls import path

import django_cas_ng.views

from users import views

app_name = 'users'
urlpatterns = [
    path('login', django_cas_ng.views.LoginView.as_view(), name='cas_ng_login'),
    path('logout', django_cas_ng.views.LogoutView.as_view(), name='cas_ng_logout'),
    path('', views.index, name='index'),

]

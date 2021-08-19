"""phylobook URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
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
from django.urls import path, include, re_path
from django.views.generic.base import RedirectView
from django.contrib import admin
from django.contrib.auth import views as auth_views
import phylobook.views as views

admin.site.site_header  =  "Phylobook Admin"
admin.site.site_title  =  "Phylobook Admin Site"
admin.site.index_title  =  "Phylobook Admin"


urlpatterns = [
    path('admin/', admin.site.urls),
    #re_path(r"^accounts/", include("django.contrib.auth.urls")),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    #path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path("password_reset", views.password_reset_request, name="password_reset"),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('password-change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path("projects/", include("phylobook.projects.urls")),
    re_path(r'^$', RedirectView.as_view(url='/projects')),
]

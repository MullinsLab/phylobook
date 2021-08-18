from django.contrib.auth.decorators import login_required
from django.urls import path, re_path

from . import views


urlpatterns = [
    path("", login_required(views.projects)),
    path("<str:name>", login_required(views.displayProject)),
    path("<str:name>/<str:file>", login_required(views.getFile)),
    path("note/update/<str:name>/<str:file>", login_required(views.updateNote)),
    path("note/read/<str:name>/<str:file>", login_required(views.readNote)),
    path("svg/update/<str:name>/<str:file>", login_required(views.updateSVG)),
    path("files/download/<str:name>", login_required(views.downloadProjectFiles)),
]


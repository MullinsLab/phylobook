from django.urls import path, re_path

from . import views


urlpatterns = [
    path("", views.convert),
    path("api/treenexusinfo", views.getTreeNexusInfo),
    path("api/treeimage", views.getTreeImage),
    path("api/downloadfiles", views.downloadFiles),
    path("getprogress", views.getProgress),
    #re_path(r'^(?P<task_id>[\w-]+)/$', views.getProgress, name='task_status')
]
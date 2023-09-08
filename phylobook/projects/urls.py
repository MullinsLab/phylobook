from django.contrib.auth.decorators import login_required
from django.urls import path, re_path

from . import views


urlpatterns = [
    path("", login_required(views.projects)),
    path("note/update/<str:name>/<str:file>", login_required(views.updateNote)),
    path("note/read/<str:name>/<str:file>", login_required(views.readNote)),
    path("svg/update/<str:name>/<str:file>", login_required(views.updateSVG)),
    path("files/download/<str:name>", login_required(views.downloadProjectFiles)),
    path("files/download/fasta/<str:name>/<str:file>", login_required(views.downloadOrderedFasta)),
    path("files/download/extractedfasta/<str:name>/<str:file>", login_required(views.downloadExtractedFasta)),
    path("settings/<str:project>/<str:tree>", views.TreeSettings.as_view(), name="tree_settings_set"),
    path("settings/<str:project>/<str:tree>/<str:setting>", views.TreeSettings.as_view(), name="tree_settings_get"),
    path("lineages", views.Lineages.as_view(), name="lineages"),
    path("lineages/<str:project>/<str:tree>", views.TreeLineages.as_view(), name="tree_lineages"),
    path("lineages/<str:project>/<str:tree>/<str:flag>", views.TreeLineages.as_view(), name="tree_lineages_flag"),
    path("lineages_ready/<str:project>", views.ProjectLineagesReady.as_view(), name="project_lineages_ready"),
    path("lineages_ready/<str:project>/<str:tree>", views.TreeLineagesReady.as_view(), name="tree_lineages_ready"),
    path("extract_to_zip/<str:project>", views.ExtractAllToZip.as_view(), name="extract_all_lineages"),
    path("extract_to_zip/<str:project>/<str:tree>", views.ExtractToZip.as_view(), name="extract_lineage"),
    path("<str:name>", login_required(views.displayProject)),
    path("<str:name>/TEST_SVG", login_required(views.displayProject), {"test_svg": True}),
    path("<str:name>/TEST_SVG<int:width>", login_required(views.displayProject), {"test_svg": True}),
    path("<str:name>/<str:file>", login_required(views.getFile)),
    path("<str:name>/<str:throw_away>/<str:file>", login_required(views.getFile)),
]


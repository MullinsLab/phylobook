import os

from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import render
from django.contrib.auth.models import Group
from pathlib import Path
from django.conf import settings

PROJECT_PATH = settings.PROJECT_PATH

def projects(request):

    context = {
        "projects": getUserProjects(request.user)
    }

    return render(request, "projects.html", context)

def displayProject(request, name):
    if request.user.groups.filter(name=name).exists():
        entries = []
        projectPath = os.path.join(PROJECT_PATH, name)
        for file in sorted(os.listdir(projectPath)):
            if file.endswith("_highlighter.png"):
                uniquesvg = file[0:file.index("_highlighter.png")]
                for svg in os.listdir(projectPath):
                    if svg.endswith(".svg"):
                        if uniquesvg in svg:
                            entries.append({"uniquesvg": uniquesvg, "svg":os.path.join(name, svg), "highlighter":os.path.join(name, file)})

        context = {
            "entries": entries,
            "project": name
        }
        return render(request, "displayproject.html", context)

    else:
        return render(request, "projects.html", { "noaccess": name, "projects": getUserProjects(request.user) })


def getUserProjects(user):
    # filter the Group model for current logged in user instance
    query_set = Group.objects.filter(user=user)

    availableProjects = []
    # print to console for debug/checking
    for g in query_set:
        # this should print all group names for the user
        availableProjects.append(g.name)  # or id or whatever Group field that you want to display


    return sorted(availableProjects)

def getFile(request, name, file):
    if request.user.groups.filter(name=name).exists():
        filePath = os.path.join(PROJECT_PATH, name, file)
        try:
            if file.endswith(".svg"):
                with open(filePath, "rt") as f:
                    return HttpResponse(f.read(), content_type="image/svg+xml")
            if file.endswith(".png"):
                with open(filePath, "rb") as f:
                    return HttpResponse(f.read(), content_type="image/png")
        except IOError:
            return HttpResponseNotFound("File not found!")
    else:
        return HttpResponseNotFound("File not found!")

def readNote(request, name, file):
    if request.user.groups.filter(name=name).exists() and request.is_ajax():
        filePath = Path(os.path.join(PROJECT_PATH, name, file))
        if filePath.is_file():
            notes = ""
            started = False
            with open(filePath, 'r') as f:
                for line in f:
                    if '[~~~~~~~~~~]' in line:
                        if not started:
                            started = True
                            continue
                        else:
                            return HttpResponse(notes)
                    notes = notes + line + '\n'
            f.close()
            return HttpResponse("Click to add notes")
        else:
            return HttpResponse("Click to add notes")
    else:
        response = HttpResponseForbidden("Permission Denied.")
        return response

def updateNote(request, name, file):
    if request.user.groups.filter(name=name).exists() and request.is_ajax():
        if request.method == 'POST':
            filePath = Path(os.path.join(PROJECT_PATH, name, file + ".notes.txt"))
            notes = request.POST.get('notes')
            if filePath.is_file():
                with open(filePath, 'r+') as f:
                    content = f.read()
                    f.seek(0, 0)
                    f.write('[~~~~~~~~~~]\n' + notes + '\n[~~~~~~~~~~]\n' + content)
                    f.close()
            else:
                f = open(filePath, "w+")
                f.write('[~~~~~~~~~~]\n' + notes + '\n[~~~~~~~~~~]\n')
                f.close()
            return HttpResponse("Note Saved.")
    else:
        response = HttpResponseForbidden("Permission Denied.")
        return response

def updateSVG(request, name, file):
    if request.user.groups.filter(name=name).exists() and request.is_ajax():
        if request.method == 'POST':
            projectPath = os.path.join(PROJECT_PATH, name)
            for f in sorted(os.listdir(projectPath)):
                if f.endswith(".svg") and f.startswith(file):
                    filePath = Path(os.path.join(PROJECT_PATH, name, f))
                    svg = request.POST.get('svg')
                    with open(filePath, "w") as f:
                        f.write(svg)
                        f.close()
                    return HttpResponse("SVG Saved.")
    else:
        response = HttpResponseForbidden("Permission Denied.")
        return response
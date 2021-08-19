import os
import tarfile
import time

from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import render
from django.contrib.auth.models import Group
from pathlib import Path
from django.conf import settings
from phylobook.models import Project
from guardian.shortcuts import get_perms

PROJECT_PATH = settings.PROJECT_PATH

def projects(request):

    context = {
        "projects": getUserProjects(request.user)
    }

    return render(request, "projects.html", context)

def displayProject(request, name):
    project = Project.objects.get(name=name)
    print(project)
    print(get_perms(request.user, project))
    if project and request.user.has_perm('phylobook.change_project', project):
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
    # filter the Project model for what the user can "change_project"
    query_set = Project.objects.all()
    availableProjects = []
    for project in query_set:
        # check permissions and add to available if user has permission
        if user.has_perm('phylobook.change_project', project):
            print(get_perms(user, project))
            availableProjects.append(project.name)

    return sorted(availableProjects)

def getFile(request, name, file):
    project = Project.objects.get(name=name)
    if project and request.user.has_perm('phylobook.change_project', project):
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
    project = Project.objects.get(name=name)
    if project and request.user.has_perm('phylobook.change_project', project) and request.is_ajax():
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
    project = Project.objects.get(name=name)
    if project and request.user.has_perm('phylobook.change_project', project) and request.is_ajax():
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
    project = Project.objects.get(name=name)
    if project and request.user.has_perm('phylobook.change_project', project) and request.is_ajax():
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

def downloadProjectFiles(request, name):
    response = HttpResponse(content_type='application/x-gzip')
    response['Content-Disposition'] = 'attachment; filename=' + name + '-' + time.strftime("%Y%m%d-%H%M%S") + '.tar.gz'
    tarred = tarfile.open(fileobj=response, mode='w:gz')
    tarred.add(os.path.join(PROJECT_PATH, name), arcname=name)
    tarred.close()

    return response



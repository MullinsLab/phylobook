import os
import tarfile
import time
import json
from datetime import datetime

from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import render
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
    if project and (request.user.has_perm('phylobook.change_project', project) or request.user.has_perm('phylobook.view_project', project)):
        entries = []
        projectPath = os.path.join(PROJECT_PATH, name)
        for file in sorted(os.listdir(projectPath)):
            if file.endswith("_highlighter.png"):
                uniquesvg = file[0:file.index("_highlighter.png")]
                for svg in os.listdir(projectPath):
                    if svg.endswith(".svg"):
                        if uniquesvg in svg:
                            filePath = Path(os.path.join(PROJECT_PATH, name, uniquesvg + ".json"))
                            clusterPath = Path(os.path.join(PROJECT_PATH, name, uniquesvg + ".cluster"))
                            clusterFile = ""
                            if clusterPath.is_file():
                                clusterFile = uniquesvg + ".cluster"
                            if filePath.is_file():
                                with open(filePath, 'r') as json_file:
                                    data = json.load(json_file)
                                    minval = data["minval"] if (data["minval"] != "None" and data["minval"] != None and data["minval"] != "") else ""
                                    maxval = data["maxval"] if (data["maxval"] != "None" and data["maxval"] != None and data["maxval"] != "") else ""
                                    colorlowval = data["colorlowval"] if (data["colorlowval"] != "None" and data["colorlowval"] != None and data["colorlowval"] != "") else ""
                                    colorhighval = data["colorhighval"] if (data["colorhighval"] != "None" and data["colorhighval"] != None and data["colorhighval"] != "") else ""
                                    iscolored = data["iscolored"] if (data["iscolored"] != "None" and data["iscolored"] != None and data["iscolored"] != "") else "false"
                                    entries.append({"uniquesvg": uniquesvg, "svg":os.path.join(name, svg), "highlighter":os.path.join(name, file), "minval": minval, \
                                                    "maxval": maxval, "colorlowval": colorlowval, "colorhighval": colorhighval, "iscolored": iscolored, "clusterfile": clusterFile})
                            else:
                                entries.append({"uniquesvg": uniquesvg, "svg": os.path.join(name, svg), "highlighter": os.path.join(name, file), "minval": "", \
                                                "maxval": "", "colorlowval": "", "colorhighval": "", "iscolored": "false", "clusterfile": clusterFile})

        context = {
            "entries": entries,
            "project": name,
            "project_obj": project
        }
        return render(request, "displayproject.html", context)

    else:
        return render(request, "projects.html", { "noaccess": name, "projects": getUserProjects(request.user) })


def getUserProjects(user):
    # filter the Project model for what the user can "change_project" or "view_project"
    query_set = Project.objects.all()
    availableProjects = []
    for project in query_set:
        # check permissions and add to available if user has permission
        if user.has_perm('phylobook.change_project', project) or user.has_perm('phylobook.view_project', project):
            availableProjects.append(project.name)

    return sorted(availableProjects)

def getFile(request, name, file):
    project = Project.objects.get(name=name)
    if project and (request.user.has_perm('phylobook.change_project', project) or request.user.has_perm('phylobook.view_project', project)):
        filePath = os.path.join(PROJECT_PATH, name, file)
        try:
            if file.endswith(".svg"):
                with open(filePath, "rt") as f:
                    return HttpResponse(f.read(), content_type="image/svg+xml")
            if file.endswith(".png"):
                with open(filePath, "rb") as f:
                    return HttpResponse(f.read(), content_type="image/png")
            if file.endswith(".cluster"):
                with open(filePath, "rt") as f:
                    return HttpResponse(f.read(), content_type="text/csv")
        except IOError:
            return HttpResponseNotFound("File not found!")
    else:
        return HttpResponseNotFound("File not found!")

def readNote(request, name, file):
    project = Project.objects.get(name=name)
    if project and \
            (request.user.has_perm('phylobook.change_project', project) or request.user.has_perm('phylobook.view_project', project)) \
            and request.is_ajax():
        filePath = Path(os.path.join(PROJECT_PATH, name, file + ".json"))
        notes = ""
        if filePath.is_file():
            with open(filePath, 'r') as json_file:
                data = json.load(json_file)
                notes = data["notes"][-1]["note"]
            return HttpResponse(notes)
        else:
            return HttpResponse(notes)
    else:
        response = HttpResponseForbidden("Permission Denied.")
        return response

def updateNote(request, name, file):
    project = Project.objects.get(name=name)
    if project and request.user.has_perm('phylobook.change_project', project) and request.is_ajax():
        if request.method == 'POST':
            filePath = Path(os.path.join(PROJECT_PATH, name, file + ".json"))
            notes = request.POST.get('notes')
            minval = request.POST.get('minval')
            maxval = request.POST.get('maxval')
            colorlowval = request.POST.get('colorlowval')
            colorhighval = request.POST.get('colorhighval')
            iscolored = request.POST.get('iscolored')
            dateTimeObj = datetime.now()
            data = {}
            data['notes'] = []
            #print("minval=" + minval + " maxval=" + maxval + " colorlowval=" + colorlowval + " colorhighval=" + colorhighval + " iscolored=" + iscolored)
            if filePath.is_file():
                with open(filePath, 'r+') as json_file:
                    data = json.load(json_file)
            with open(filePath, "w+") as outfile:
                data['notes'].append({
                    'note': notes,
                    'user': request.user.username,
                    'datetime': str(dateTimeObj)
                })
                data['minval'] = minval
                data['maxval'] = maxval
                data['colorlowval'] = colorlowval
                data['colorhighval'] = colorhighval
                data['iscolored'] = iscolored
                json.dump(data, outfile)

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
    project = Project.objects.get(name=name)
    if project and (request.user.has_perm('phylobook.change_project', project) or request.user.has_perm('phylobook.view_project', project)):
        response = HttpResponse(content_type='application/x-gzip')
        response['Content-Disposition'] = 'attachment; filename=' + name + '-' + time.strftime("%Y%m%d-%H%M%S") + '.tar.gz'
        tarred = tarfile.open(fileobj=response, mode='w:gz')
        tarred.add(os.path.join(PROJECT_PATH, name), arcname=name)
        tarred.close()
    else:
        response = HttpResponseForbidden("Permission Denied.")
        return response

    return response



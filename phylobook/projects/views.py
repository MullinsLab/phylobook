import logging
log = logging.getLogger('app')

import os, tarfile, time, json, mimetypes, glob
from io import StringIO
from datetime import datetime

from Bio import SeqIO
from Bio.SeqIO.FastaIO import SimpleFastaParser
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound, JsonResponse, FileResponse
from django.shortcuts import render
from pathlib import Path
from django.conf import settings
from guardian.shortcuts import get_perms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import View

from phylobook.projects.models import Project, ProjectCategory, Tree
from phylobook.projects.utils import fasta_type, tree_lineage_counts, svg_file_name, get_lineage_dict

PROJECT_PATH = settings.PROJECT_PATH


def projects(request):

    context = {
        # "projects": getUserProjects(request.user)
        "project_tree": get_user_project_tree(request.user)
    }

    return render(request, "projects.html", context)


def displayProject(request, name):
    project = Project.objects.get(name=name)
    if project and (request.user.has_perm('projects.change_project', project) or request.user.has_perm('projects.view_project', project)):
        entries = []
        projectPath = os.path.join(PROJECT_PATH, name)

        for file in sorted(os.listdir(projectPath)):
            if file.endswith("_highlighter.png"):
                uniquesvg = file[0:file.index("_highlighter.png")]
                for svg in os.listdir(projectPath):
                    if svg.endswith(".svg"):
                        if uniquesvg in svg:
                            filePath = Path(os.path.join(PROJECT_PATH, name, uniquesvg + ".json"))
                            prefix = uniquesvg + ".cluster"

                            try:
                                tree = project.trees.get(name=uniquesvg)
                            except Tree.DoesNotExist:
                                tree = project.trees.create(name=uniquesvg)

                            if not tree.type:
                                tree.type = fasta_type(tree=tree)
                                tree.save()

                            if filePath.is_file():
                                with open(filePath, 'r') as json_file:
                                    data = json.load(json_file)
                                    minval = data["minval"] if (data["minval"] != "None" and data["minval"] != None and data["minval"] != "") else ""
                                    maxval = data["maxval"] if (data["maxval"] != "None" and data["maxval"] != None and data["maxval"] != "") else ""
                                    colorlowval = data["colorlowval"] if (data["colorlowval"] != "None" and data["colorlowval"] != None and data["colorlowval"] != "") else ""
                                    colorhighval = data["colorhighval"] if (data["colorhighval"] != "None" and data["colorhighval"] != None and data["colorhighval"] != "") else ""
                                    iscolored = data["iscolored"] if (data["iscolored"] != "None" and data["iscolored"] != None and data["iscolored"] != "") else "false"
                                    entries.append({"uniquesvg": uniquesvg, "svg":os.path.join(name, svg), "highlighter":os.path.join(name, file), "minval": minval, \
                                                    "maxval": maxval, "colorlowval": colorlowval, "colorhighval": colorhighval, "iscolored": iscolored, "clusterfiles": getClusterFiles(projectPath, prefix), "tree": tree})
                            else:
                                entries.append({"uniquesvg": uniquesvg, "svg": os.path.join(name, svg), "highlighter": os.path.join(name, file), "minval": "", \
                                                "maxval": "", "colorlowval": "", "colorhighval": "", "iscolored": "false", "clusterfiles": getClusterFiles(projectPath, prefix), "tree": tree})

        context = {
            "entries": entries,
            "project": name,
            "project_obj": project
        }
        return render(request, "displayproject.html", context)

    else:
        return render(request, "projects.html", { "noaccess": name, "projects": get_user_project_tree(request.user) })


def getClusterFiles(projectPath, prefix):
    clusters = []
    for file in sorted(os.listdir(projectPath)):
        if file.startswith(prefix):
            name = file[file.index(".cluster.") + 9:]
            clusters.append({ "name": name, "file": file})
    return clusters


def get_user_projects(user):
    # filter the Project model for what the user can "change_project" or "view_project"
    query_set = Project.objects.all()
    availableProjects = []
    for project in query_set:
        # check permissions and add to available if user has permission
        if user.has_perm('projects.change_project', project) or user.has_perm('projects.view_project', project):
            availableProjects.append(project.name)
    return sorted(availableProjects)


def get_user_project_tree(user) -> dict:
    """ Loads the Projects that a User can see, along with their categories """
    projects_tree = []

    # Start by getting projects that don't have a category
    query_set = Project.objects.filter(category=None)

    for project in query_set:
        project.tree_node(user=user, list=projects_tree)

    for category in ProjectCategory.get_root_nodes():
        category.tree_node(user=user, list=projects_tree)
    
    return projects_tree


def getFile(request, name, file):
    project = Project.objects.get(name=name)
    if project and (request.user.has_perm('projects.change_project', project) or request.user.has_perm('projects.view_project', project)):
        filePath = os.path.join(PROJECT_PATH, name, file)
        try:
            if file.endswith(".svg"):
                with open(filePath, "rt") as f:
                    return HttpResponse(f.read(), content_type="image/svg+xml")
            elif file.endswith(".png"):
                with open(filePath, "rb") as f:
                    return HttpResponse(f.read(), content_type="image/png")
            elif ".cluster" in file:
                with open(filePath, "rt") as f:
                    lines = f.readlines()
                    cleaned = ""
                    for line in lines:
                        line = cleanClusterRow(line)
                        cleaned = cleaned + line
                    return HttpResponse(cleaned, content_type="text/csv")
        except IOError:
            log.warn(f"Error: File not found: {file}")
            return HttpResponseNotFound("File not found!")
    else:
        log.warn(f"Error: File not found: {file}")
        return HttpResponseNotFound("File not found!")


def cleanClusterRow(row):
    """ removes commas that aren't separating fields """
    commaCount = row.count(",")
    while commaCount > 1:
        row = "".join(row.rsplit(",", 1))
        commaCount = row.count(",")
    return row;


def readNote(request, name, file):
    project = Project.objects.get(name=name)
    if project and \
            (request.user.has_perm('projects.change_project', project) or request.user.has_perm('projects.view_project', project)) \
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
        log.warn(f"Error: Permission denied: {file}")
        response = HttpResponseForbidden("Permission Denied.")
        return response


def updateNote(request, name, file):
    project = Project.objects.get(name=name)
    if project and request.user.has_perm('projects.change_project', project) and request.is_ajax():
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
            #log.warn("minval=" + minval + " maxval=" + maxval + " colorlowval=" + colorlowval + " colorhighval=" + colorhighval + " iscolored=" + iscolored)
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
        log.warn(f"Error: Permission denied: {file}")
        response = HttpResponseForbidden("Permission Denied.")
        return response


def updateSVG(request, name, file):
    project = Project.objects.get(name=name)
    if project and request.user.has_perm('projects.change_project', project) and request.is_ajax():
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
        log.warn(f"Error: Permission denied: {file}")
        response = HttpResponseForbidden("Permission Denied.")
        return response


def downloadProjectFiles(request, name):
    project = Project.objects.get(name=name)
    if project and (request.user.has_perm('projects.change_project', project) or request.user.has_perm('projects.view_project', project)):
        response = HttpResponse(content_type='application/x-gzip')
        response['Content-Disposition'] = 'attachment; filename=' + name + '-' + time.strftime("%Y%m%d-%H%M%S") + '.tar.gz'
        tarred = tarfile.open(fileobj=response, mode='w:gz')
        tarred.add(os.path.join(PROJECT_PATH, name), arcname=name)
        tarred.close()
    else:
        log.warn(f"Error: Permission denied: {name}")
        response = HttpResponseForbidden("Permission Denied.")
        return response

    return response


def downloadOrderedFasta(request, name, file):
    project = Project.objects.get(name=name)
    if project and (request.user.has_perm('projects.change_project', project) or request.user.has_perm('projects.view_project', project)):
        orderedFasta = buildOrderedFastaFile(name, file)
        response = HttpResponse(orderedFasta, content_type='application/x-fasta')
        response['Content-Disposition'] = 'attachment; filename=' + file + '-ordered.fasta'
    else:
        log.warn(f"Error: Permission denied: {file}")
        response = HttpResponseForbidden("Permission Denied.")

    return response


def buildOrderedFastaFile(name, file):
    log.debug("buildOrderedFastaFile: " + name + " " + file)
    highlighterFastaFile = glob.glob(os.path.join(PROJECT_PATH, name, file + "*_highlighter.fasta"))
    orderedFasta = ""
    # check to see if ordered highlighter provided fasta is available
    if len(highlighterFastaFile) > 0:
        file = open(highlighterFastaFile[0], "r")
        orderedFasta = file.read()
        file.close()
        return orderedFasta
    fastaFile = glob.glob(os.path.join(PROJECT_PATH, name, file + "*.fasta"))
    highlighterDataFile = glob.glob(os.path.join(PROJECT_PATH, name, file + "*_highlighter.txt"))
    if len(fastaFile) > 0 and len(highlighterDataFile) > 0:
        recordDict = SeqIO.index(fastaFile[0], "fasta")
        highlighterData = open(highlighterDataFile[0], 'r')
        # log.debug(highlighterData)

        while True:
            record = readNextHighlighterRecord(highlighterData)
            if record is None:
                break
            else:
                name = record["name"].strip()
                orderedFasta = orderedFasta + recordDict.get_raw(name).decode()
        return orderedFasta
    else:
        return None


def readNextHighlighterRecord(highlighterData):
    # log.debug("readNextHighlighterRecord")

    seqName = highlighterData.readline()
    if seqName is None or seqName == '':
        return None;
    annotations = []
    while True:
        line = highlighterData.readline()
        if line == "\n" or line == "" or line is None:
            break
        else:
            annotations.append(line)
    return {"name": seqName, "annotations": annotations}


def downloadExtractedFasta(request, name, file):
    project = Project.objects.get(name=name)
    if request.method == 'POST' and project and (request.user.has_perm('projects.change_project', project) or request.user.has_perm('projects.view_project', project)):
        seqsVal = request.POST.get('seqs')
        seqs = []
        if seqsVal and "," in seqsVal:
            seqs = request.POST.get('seqs').split(",")
        else:
            seqs.append(seqsVal)
        suffix = request.POST.get('suffix')
        orderedFasta = buildOrderedFastaFile(name, file)
        fastaIO = StringIO(orderedFasta)
        records = SeqIO.parse(fastaIO, "fasta")
        extractedsSeqs = ""
        for rec in records:
            if rec.id in seqs:
                extractedsSeqs = extractedsSeqs + ">" + rec.id + suffix + "\n" + rec.seq + "\n"
        fastaIO.close()

        response = HttpResponse(extractedsSeqs, content_type='text/plain')
        return response
    else:
        log.warn(f"Error: Permission denied: {file}")
        response = HttpResponseForbidden("Permission Denied.")
        return response
    

class TreeSettings(LoginRequiredMixin, View):
    """ Class to get or set settings for a tree """

    def get(self, request, *args, **kwargs):
        """ Get a JSON dictionary for a setting, or settings """
        
        return_data: dict = {}

        project_name: str = kwargs["project"]
        project: Project = Project.objects.filter(name=project_name).first()

        tree_name: str = kwargs["tree"]
        try:
            tree: Tree = Tree.objects.get(project=project, name=tree_name)
        except:
            return JsonResponse(return_data)

        setting = kwargs["setting"]

        if tree.settings:
            return_data = tree.settings.get(setting, {})
        else:
            return_data = {}

        return JsonResponse(return_data)

    def post(self, request, *args, **kwargs):
        """ Save settings recieved as a JSON dictionary """

        project_name: str = kwargs["project"]
        project = Project.objects.filter(name=project_name).first()

        tree_name: str = kwargs["tree"]
        settings = json.load(request)

        tree, created = Tree.objects.get_or_create(project=project, name=tree_name)
        if tree.settings == None: tree.settings = {}
        
        for setting, value in settings.items():
            if value == None:
                tree.settings.pop(setting)
            else:
                tree.settings[setting] = value

        tree.save()

        return_data = {'saved': True}
        
        return JsonResponse(return_data)
    

class Lineages(LoginRequiredMixin, View):
    """ Get the full list of lineages """

    def get(self, request, *args, **kwargs):
        """ Return the list of lineages """

        return JsonResponse(get_lineage_dict())
        #return {}
    

class TreeLineages(LoginRequiredMixin, View):
    """ Get and set the lineages for a tree """

    def get(self, request, *args, **kwargs):
        """ Return information about the tree lineages to the client """

        project_name: str = kwargs["project"]
        project: Project = Project.objects.get(name=project_name)

        if not project or not (request.user.has_perm('projects.change_project', project) or request.user.has_perm('projects.view_project', project)):
            return render(request, "projects.html", {"noaccess": project_name, "projects": get_user_project_tree(request.user)})

        tree_name: str = kwargs["tree"]
        tree: Tree = Tree.objects.get(project=project, name=tree_name)
        tree_file: str = svg_file_name(project=project, tree=tree)
        
        tree_lineage: dict = tree_lineage_counts(tree_file)
        tree_settings_lineages: dict = tree.settings.get("lineages", {})

        for color in [color for color in tree_lineage if color in tree_settings_lineages]:
            tree_lineage[color]["name"] = tree.settings["lineages"][color]

        for color in [color for color in tree_settings_lineages if color not in tree_lineage]:
            tree_lineage[color] = {"name": tree_settings_lineages[color]}

        return JsonResponse(tree_lineage)
    
class ExtractToZip(LoginRequiredMixin, View):
    """ Extract sequences to a zip file by lineage """

    def get(self, request, *args, **kwargs):
        """ Return the zip file """

        project_name: str = kwargs["project"]
        project: Project = Project.objects.get(name=project_name)

        if not project or not (request.user.has_perm('projects.change_project', project) or request.user.has_perm('projects.view_project', project)):
            return render(request, "projects.html", {"noaccess": project_name, "projects": get_user_project_tree(request.user)})

        tree_name: str = kwargs["tree"]
        tree: Tree = Tree.objects.get(project=project, name=tree_name)

        return FileResponse(tree.extract_all_lineages_to_zip(), as_attachment=True, filename=f"{project.name}.zip")

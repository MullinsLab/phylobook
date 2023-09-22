import logging
log = logging.getLogger('app')

import os, tarfile, time, json, glob, time
from io import StringIO
from datetime import datetime
from pathlib import Path

from Bio import SeqIO
from Bio.SeqIO.FastaIO import SimpleFastaParser
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound, JsonResponse, FileResponse, HttpResponseBadRequest
from django.shortcuts import render
from pathlib import Path
from django.conf import settings
from guardian.shortcuts import get_perms
from django.views.generic.base import View
from django.db.models import QuerySet

from phylobook.projects.mixins import LoginRequredSimpleErrorMixin
from phylobook.projects.models import Project, ProjectCategory, Tree
from phylobook.projects.utils import fasta_type, get_lineage_dict, ensure_project_highlighter_svgs

PROJECT_PATH = settings.PROJECT_PATH


def projects(request):
    context = {
        "project_tree": get_user_project_tree(request.user)
    }

    return render(request, "projects.html", context)


def displayProject(request, name, width: int=None, start: int=None, end: int=None, test_svg=False):
    project = Project.objects.get(name=name)
    if project and (request.user.has_perm('projects.change_project', project) or request.user.has_perm('projects.view_project', project)):

        entries = []
        projectPath = os.path.join(PROJECT_PATH, name)

        #file: list = []
        tree_count: int = 0

        try:
            files = os.listdir(projectPath)
        except Exception as e:
            log.warning(f"Error reading project directory: {e}")
            return HttpResponseBadRequest(f"Error reading project directory (probably due to permissions): {projectPath}")

        if start is None and end is None:
            start = 1
            end = settings.TREES_PER_PAGE
            
        if start > 0 and end >= start:
            if end > project.trees.all().count():
                end = project.trees.all().count()
            trees: QuerySet = project.trees.all()[start-1:end]
        else:
            trees: bool = False

        for file in sorted(files):
            if file.endswith("_highlighter.png"):
                uniquesvg = file[0:file.index("_highlighter.png")]
                                        
                for svg in os.listdir(projectPath):
                    if svg.endswith(".svg") and "_highlighter." not in svg and "_match." not in svg:
                        if uniquesvg in svg:
                            filePath = Path(os.path.join(projectPath, uniquesvg + ".json"))

                            prefix = uniquesvg + ".cluster"

                            try:
                                tree = project.trees.get(name=uniquesvg)
                            except Tree.DoesNotExist:
                                tree = project.trees.create(name=uniquesvg)

                            tree_count += 1

                            if trees and tree not in trees:
                                continue

                            if not tree.type:
                                tree.type = fasta_type(tree=tree)
                                tree.save()

                            if tree.has_svg_highlighter(width=settings.HIGHLIGHTER_MARK_WIDTH, no_build=True):
                                file = tree.highlighter_file_name_svg(width=settings.HIGHLIGHTER_MARK_WIDTH, path=False)

                            data = None

                            if filePath.is_file():
                                try:
                                    with open(filePath, 'r') as json_file:
                                        data = json.load(json_file)
                                except:
                                    pass

                            if data:      
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

        # previous_start: int
        # previous_end: int

        pages: list = project.pages()

        if start == 1:
            previous_url = None
            first_url = None
        else:
            previous_start = ((int(start/settings.TREES_PER_PAGE)-1)*settings.TREES_PER_PAGE)+1
            previous_end = previous_start + settings.TREES_PER_PAGE - 1
            previous_url = f"/projects/{name}/{previous_start}-{previous_end}"

            first_url = pages[0][1]

        if not previous_url:
            next_start = settings.TREES_PER_PAGE+1
            next_end = settings.TREES_PER_PAGE*2
        else:
            next_start = previous_end + settings.TREES_PER_PAGE + 1
            next_end = next_start + settings.TREES_PER_PAGE - 1

        if next_end > tree_count:
            next_end = tree_count

        if next_start > tree_count:
            next_url = None
        else:
            next_url = f"/projects/{name}/{next_start}-{next_end}"

        if end == tree_count:
            last_url = None
        else:
            last_url: str = pages[-1][1]

        context = {
            "entries": entries,
            "project": name,
            "project_obj": project, 
            "tree_count": tree_count,
            "range": f"{start}-{end} of " if trees else "",
            "previous_url": previous_url,
            "next_url": next_url,
            "first_url": first_url,
            "last_url": last_url,
            "pages": pages,
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

class MatchImage(LoginRequredSimpleErrorMixin, View):
    """ Returns the match image for a tree """

    def get(self, request, *args, **kwargs):
        """ Return the match image """

        project_name: str = kwargs["project"]
        project: Project = Project.objects.get(name=project_name)

        if not project or not (request.user.has_perm('projects.change_project', project) or request.user.has_perm('projects.view_project', project)):
            return render(request, "projects.html", {"noaccess": project_name, "projects": get_user_project_tree(request.user)})

        tree_name: str = kwargs["tree"]
        tree: Tree = Tree.objects.get(project=project, name=tree_name)

        if tree.has_svg_match():
            # log.debug("Got match image")
            return FileResponse(open(tree.match_file_name_svg(), "rb"), content_type="image/svg+xml")
        else:
            # log.debug("No match image")
            return FileResponse(open("/phylobook/phylobook/static/images/empty_match.svg", "rb"), content_type="image/svg+xml")

def getFile(request, name, file, **kwargs):
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
                
            else:
                tree = project.trees.get(name=file)
                filePath = tree.svg_file_name
                
                with open(filePath, "rt") as f:
                    return HttpResponse(f.read(), content_type="image/svg+xml")
                
        except IOError:
            log.warn(f"Error: File not found: {filePath}")
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
            
            if filePath.is_file():
                try: 
                    with open(filePath, 'r+') as json_file:
                        data = json.load(json_file)
                except PermissionError:
                    log.warn(f"Error: Permission denied: {filePath}")
                    return HttpResponseForbidden(f"\nPermission Denied for file: '{file}'.")

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


def updateSVG(request, project_name, tree_name):
    project: Project = Project.objects.get(name=project_name)
    tree: Tree = project.trees.get(name=tree_name)
    
    if project and request.user.has_perm('projects.change_project', project) and request.is_ajax():
        if request.method == 'POST':
            # projectPath = os.path.join(PROJECT_PATH, project_name)
            # for f in sorted(os.listdir(projectPath)):
            #     if f.endswith(".svg") and f.startswith(tree_name):
            #         filePath = Path(os.path.join(PROJECT_PATH, project_name, f))
            #         log.debug(f"Filepath: {tree.svg_file_name}")
            svg = request.POST.get('svg')
            
            try:
                with open(tree.svg_file_name, "w") as f:
                    f.write(svg)
                    f.close()
                return HttpResponse("SVG Saved.")
            except PermissionError:
                log.warn(f"Error: Permission denied: {tree.svg_file_name}")
                return HttpResponseForbidden(f"\nPermission Denied for file: '{tree_name}'.")
    else:
        log.warn(f"Error: Permission denied: {tree_name}")
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
    

class TreeSettings(LoginRequredSimpleErrorMixin, View):
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
                if setting == "lineages":
                    Path(tree.svg_file_name).touch()

        tree.save()

        return_data = {'saved': True}
        
        return JsonResponse(return_data)
    

class Lineages(LoginRequredSimpleErrorMixin, View):
    """ Get the full list of lineages """

    def get(self, request, *args, **kwargs):
        """ Return the list of lineages """

        return JsonResponse(get_lineage_dict())
    

class TreeLineages(LoginRequredSimpleErrorMixin, View):
    """ Get and set the lineages for a tree """
    
    def get(self, request, *args, **kwargs):
        """ Return information about the tree lineages to the client """

        flag = kwargs.get("flag")

        project_name: str = kwargs["project"]
        project: Project = Project.objects.get(name=project_name)

        if not project or not (request.user.has_perm('projects.change_project', project) or request.user.has_perm('projects.view_project', project)):
            return render(request, "projects.html", {"noaccess": project_name, "projects": get_user_project_tree(request.user)})

        tree_name: str = kwargs["tree"]
        tree: Tree = Tree.objects.get(project=project, name=tree_name)

        if not tree.fasta_file_name:
            return JsonResponse({"error": "This tree does not have an associate .fasta file.  Extractions can not be performed on it."})

        tree.load_svg_tree()
        tree_lineage: dict = tree.phylotree.lineage_counts
        
        if swap_message := tree.swap_by_counts():
            if flag == "recolor":
                tree.save_file()
                
                for color in tree_lineage.keys():
                    if color in [setting_color["short"] for setting_color in settings.ANNOTATION_COLORS if setting_color['has_UOLs']]:
                        if "warnings" not in tree_lineage:
                            tree_lineage["warnings"] = []

                        tree_lineage["warnings"].append(f"This tree may contain UOLs. Please ensure that UOL designations match the correct major lineage after being recolored.")
                        break

        if not tree.settings:
            tree_settings_lineages: dict = {}
        else:
            tree_settings_lineages: dict = tree.settings.get("lineages", {})

        for color in [color for color in tree_lineage if color in tree_settings_lineages]:
            tree_lineage[color]["name"] = tree.settings["lineages"][color]

        for color in [color for color in tree_settings_lineages if color not in tree_lineage]:
            tree_lineage[color] = {"name": tree_settings_lineages[color]}

        if swap_message:
            tree_lineage["swap_message"] = swap_message

        if tree.unassigned_sequences:
            if "warnings" not in tree_lineage:
                tree_lineage["warnings"] = []
            
            tree_lineage["warnings"].append(f"{tree.unassigned_sequences} sequence(s) have not been assigned to a lineage.")

        return JsonResponse(tree_lineage)
    
class TreeLineagesReady(LoginRequredSimpleErrorMixin, View):
    """ Check if the tree lineages are ready for extraction """

    def get(self, request, *args, **kwargs):
        """ Return true if the lineage is ready"""
    
        project_name: str = kwargs["project"]
        project: Project = Project.objects.get(name=project_name)

        if not project or not (request.user.has_perm('projects.change_project', project) or request.user.has_perm('projects.view_project', project)):
            return HttpResponseBadRequest(f"Error loading this project while trying to establish whether the lineage is ready extract: {project_name}")
    
        tree_name: str = kwargs["tree"]
        tree: Tree = Tree.objects.get(project=project, name=tree_name)

        ready: dict = {"assigned": tree.ready_to_extract}

        return JsonResponse(ready)


class ProjectLineagesReady(LoginRequredSimpleErrorMixin, View):
    """ Check if the project lineages are ready for extraction """

    def get(self, request, *args, **kwargs):
        """ return the ready object as json """

        project_name: str = kwargs["project"]
        project: Project = Project.objects.get(name=project_name)

        if not project or not (request.user.has_perm('projects.change_project', project) or request.user.has_perm('projects.view_project', project)):
            return HttpResponseBadRequest(f"Error loading this project while trying to establish whether the lineage is ready extract: {project_name}")

        return JsonResponse(project.ready_to_extract())

    
class ExtractAllToZip(LoginRequredSimpleErrorMixin, View):
    """ Extract all tree sequences to a zip file by lineage """

    def get(self, request, *args, **kwargs):
        """ Return the zip file """

        project_name: str = kwargs["project"]
        project: Project = Project.objects.get(name=project_name)

        if not project or not (request.user.has_perm('projects.change_project', project) or request.user.has_perm('projects.view_project', project)):
            return render(request, "projects.html", {"noaccess": project_name, "projects": get_user_project_tree(request.user)})
        
        response = HttpResponse(project.extract_all_trees_to_zip(), content_type="application/force-download")
        response["Content-Disposition"] = f'attachment; filename="{project.name}_extracted_lineages.zip"'
        return response
    

class ExtractToZip(LoginRequredSimpleErrorMixin, View):
    """ Extract sequences to a zip file by lineage """

    def get(self, request, *args, **kwargs):
        """ Return the zip file """

        project_name: str = kwargs["project"]
        project: Project = Project.objects.get(name=project_name)

        if not project or not (request.user.has_perm('projects.change_project', project) or request.user.has_perm('projects.view_project', project)):
            return render(request, "projects.html", {"noaccess": project_name, "projects": get_user_project_tree(request.user)})

        tree_name: str = kwargs["tree"]
        tree: Tree = Tree.objects.get(project=project, name=tree_name)

        response = HttpResponse(tree.extract_all_lineages_to_zip(), content_type="application/force-download")
        response["Content-Disposition"] = f'attachment; filename="{tree.name}_extracted_lineages.zip"'
        return response

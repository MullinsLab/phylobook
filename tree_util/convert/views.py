import json
import subprocess
import tempfile
import tree_util.convert.tasks
from Bio import Phylo
from django.http import HttpResponseServerError, HttpResponse, JsonResponse, FileResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from io import StringIO
from PIL import Image
from django.template import RequestContext
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from celery.result import AsyncResult

def convert(request):

    context = {

    }

    return render(request, "convert.html", context)

def getProgress(request):
    result = tree_util.convert.tasks.my_task.delay(10)
    return render(request, 'display_progress.html', context={'task_id': result.task_id})

def downloadFiles(request):
    # the .delay() call here is all that's needed
    # to convert the function to be called asynchronously
    tree_util.convert.tasks.my_task.delay()
    # we can't say 'work done' here anymore because all we did was kick it off
    return HttpResponse('work kicked off!')

@csrf_exempt
def getTreeNexusInfo(request):
    defaultcolors = ["#000000", "#0000ff", "#ff00ff", "#ffa500", "#008000"]
    if request.is_ajax():
        if request.method == 'POST':
            for filename, file in request.FILES.items():
                name = request.FILES[filename].name
                colorassignments = parseColorsFromFileName(name, defaultcolors)
                treedata = request.FILES[filename].read()
                newickhandle = StringIO(treedata.decode("utf-8"))
                nexushandle = StringIO()
                Phylo.convert(newickhandle, "newick", nexushandle, "nexus")
                nexustreestring = addColorToTaxLabels(nexushandle.getvalue(), colorassignments)
                #tree.ladderize()
                #nexushandle.seek(0)
                #nexustree = Phylo.read(nexushandle, "nexus")
                #print(str(len(nexustree.get_terminals())))
                #coloredtree = colorizeTree(nexustree, colorassignments)
                #coloredtreehandle = StringIO()
                #Phylo.write(coloredtree, coloredtreehandle, "nexus")
                #print(coloredtreehandle.getvalue())
                #Phylo.convert(StringIO(newicktree.getvalue()), "newick", nexushandle, "nexus")
                #print(nexushandle.getvalue())
                #nexustree = Phylo.read(nexushandle, "nexus")

                treeinfo = {}
                treeinfo["nexus"] = nexustreestring
                treeinfo["name"] = name
                treeinfo["colors"] = colorassignments
                #print(json.dumps(treeinfo))
    return JsonResponse(treeinfo)

@csrf_exempt
def getTreeImage(request):
    print(">>>>>>>>>>>>>>>>>>>>>")
    if request.is_ajax():
        if request.method == 'POST':
            treestring = request.POST.get('tree')
            colorstring = request.POST.get('colors')
            tmp = tempfile.NamedTemporaryFile('w+t')

            try:
                # Print message before writing
                print('Write data to temporary file...')
                # Write data to the temporary file
                tmp.write(treestring)
                runparams = ['java', '-jar', '/Users/jfurlong/dev/FigTree-command-line/figtree.jar', '-settings', '/Users/jfurlong/dev/FigTree-command-line/GP.settings']

                if colorstring and colorstring != '':
                    runparams.append('-colors')
                    runparams.append(colorstring)

                runparams += ['-stdout', '-graphic', 'SVG', '-height', '768', '-width', '783', tmp.name]
                print(" ".join(runparams));
                proc = subprocess.run(runparams,
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                #encodedstring = base64.b64encode(proc.stdout)
                return HttpResponse(proc.stdout)


            except:
                red = Image.new('RGBA', (1, 1), (255, 0, 0, 0))
                response = HttpResponse(content_type="image/jpeg")
                red.save(response, "JPEG")
                return response


def colorizeTree(tree, colorassignments):
    for node in tree.get_terminals():
        print("node: " + node.get_data())
        for key in colorassignments:
            print("key: " + key)
            if key in node.name:
                print(key + " is in " + node.name)
                node.color = colorassignments[key]
                print("setting " + node.name + " " + str(node.color))
    return tree

def addColorToTaxLabels(treestring, colorassignments):
    labelsstring = treestring[treestring.index("TaxLabels ") + 9:treestring.index(";\nEnd")]
    labels = labelsstring.split(" ")
    newlabels = []
    for label in labels:
        for key in colorassignments:
            if key in label:
                newlabels.append(label + "[&!color=" + colorassignments[key] + "]")
    newlabelsstring = " ".join(newlabels)
    return treestring.replace(labelsstring, " " + newlabelsstring + " ")

def parseColorsFromFileName(filename, defaultcolors):
    colorassignments = {}
    if "-" in filename:
        start = filename.rindex("_", 0, filename.index("-"))
        sample = filename[0:start]
        end = filename.index("_", start+1, len(filename))
        timepointstring = filename[start+1:end]
        timepoints = timepointstring.split("-")
        for index in range(len(timepoints)):
            pattern = sample + "_" + timepoints[index]
            colorassignments[pattern] = defaultcolors[index]
    return colorassignments



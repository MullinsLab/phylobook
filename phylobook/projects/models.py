import logging
log = logging.getLogger('app')

import io, zipfile, shutil, datetime, os

from Bio import SeqIO
from typing import Union

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

from treebeard.mp_tree import MP_Node

# from phylobook.projects.utils import svg_file_name, fasta_file_name, tree_lineage_counts


class Lineage(models.Model):
    """ Stores global lineage information"""

    color = models.CharField(max_length=256)
    lineage_name = models.CharField(max_length=256)

    class Meta:
        verbose_name_plural = "Lineages"
        unique_together = ("color", "lineage_name")


class Project(models.Model):
    """ Projects corrispond with directories in PROJECT_PATH to load lineage data. """

    name = models.CharField(max_length=256)
    category = models.ForeignKey("ProjectCategory", null=True, blank=True, on_delete=models.SET_NULL)
    description = models.TextField(null=True, blank=True)
    edit_locked = models.BooleanField(default=False)

    def __str__(self):
        """ Returns the Name of the project for print() """
        return self.name

    def tree_node(self, list: list=[], user=None, depth: int=0) -> dict:
        """ Returns the tree node for the displayed list of nodes of Projects and Categories """

        # If a user is supplied, check if they can see this project
        if user is None or user.has_perm('projects.change_project', self) or user.has_perm('projects.view_project', self):
            list.append({self.name: {'depth': depth+1, 'is_project': True, 'description': self.description}})

        return list
    
    def ready_to_extract(self) -> dict[str: any]:
        """ Returns a list of trees and whether they're ready to extract or not """

        ready: dict[str: any] = {"ready": True, "ready_trees": [], "not_ready_trees": []}

        for tree in self.trees.all():
            if tree.ready_to_extract:
                ready["ready_trees"].append(tree.name)
            else:
                ready["not_ready_trees"].append(tree.name)

        if len(ready["not_ready_trees"]) > 0:
            ready["ready"] = False

        return ready
    
    def extract_all_trees_to_zip(self) -> io.BytesIO:
        """ Extract all the trees belonging to this project to a zip file """

        mem_zip = io.BytesIO()
        with zipfile.ZipFile(mem_zip, mode="w",compression=zipfile.ZIP_DEFLATED) as zipped_lineages:

            for tree in self.trees.all():
                lineages = tree.extract_all_lineages_to_fasta()
            
                for lineage_name, lineage in tree.extract_all_lineages_to_fasta(sort="tree").items():
                    zipped_lineages.writestr(os.path.join(tree.name, f"{tree.name}_sorted_by_tree_position", f"{tree.name}_{lineage_name}.fasta"), lineage)

                for lineage_name, lineage in tree.extract_all_lineages_to_fasta(sort="timepoint_frequency").items():
                    zipped_lineages.writestr(os.path.join(tree.name, f"{tree.name}_sorted_by_frequency", f"{tree.name}_{lineage_name}.fasta"), lineage)

                zipped_lineages.writestr(os.path.join(tree.name, f"{tree.name}_lineage_summary.csv"), tree.lineage_info_csv())

        return mem_zip.getvalue()


class ProjectCategory(MP_Node):
    """ A hierarchical node for categorizing Projects to display them in a colapsing tree """
    
    name = models.CharField(max_length=256) 
    node_order_by = ['name']

    class Meta:
        verbose_name_plural = "Project Categories"

    def __str__(self):
        """ Returns the Name of the category for print() """
        return self.name
    
    def display_for_user(self, user) -> bool:
        """ Recursive function to show if ProjectCategory should show for a specific user based on showing or editing the Project. """

        # Step through each project in this category and return True if they can view or edit it.
        for project in self.project_set.all():
            if user.has_perm('projects.change_project', project) or user.has_perm('projects.view_project', project):
                return True
        
        # Step through each child of this category and return True if they should be shown
        for child in self.get_children():
            if child.display_for_user(user): return True
        
        return False

    def tree_node(self, list: list=[], user=None, depth: int=0) -> dict:
        """ Returns the tree node for the displayed list of nodes of Projects and Categories """

        # If a user is supplied, check if they can see this project
        if user is None or self.display_for_user(user=user):
            children = []
            list.append({self.name: {'depth': depth+1, 'is_project': False, 'children': children}})

            for category in self.get_children():
                category.tree_node(user=user, depth=depth+1, list=children)
                
            for project in self.project_set.all():
                project.tree_node(user=user, depth=depth+1, list=children)
            
        return list
    

class Tree(models.Model):
    """ An object that holds information about a specific tree in a project """

    TYPE_CHOICES: set[tuple] = (("Amino Acids", "Amino Acids"), ("Nucleotides", "Nucleotides"), ("Unknown", "Unknown"))

    name = models.CharField(max_length=256)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='trees')
    settings = models.JSONField(null=True, blank=True)
    type = models.CharField(max_length=256, choices=TYPE_CHOICES, null=True, blank=True)

    class Meta:
        unique_together = ('project', 'name',)

    def __str__(self):
        """ Returns the name of the tree for print() """
        return self.name
    
    phylotree = None
    
    @property
    def unassigned_sequences(self) -> int:
        """ Returns the number of unassigned sequences in the tree """

        if not self.phylotree:
            self.phylotree.load_file()

        return self.phylotree.unassigned_sequences

    @property
    def svg_file_name(self) -> str:
        """ Returns the name of the SVG file for the tree """

        return svg_file_name(project=self.project, tree=self)
    
    @property
    def fasta_file_name(self) -> str:
        """ Returns the name of the FASTA file for the tree """

        return fasta_file_name(project=self.project, tree=self)
    
    @property
    def ready_to_extract(self) -> bool:
        """ Returns true if the tree is ready to extract lineages from """

        if self.lineage_counts():
            return True

        return False
    
    @property
    def sample_name(self) -> str:
        """ Returns the name of the sample """

        name_bits = self.name.split("_")

        if len(name_bits) == 1:
            return self.name

        return f"{name_bits[0]}_{name_bits[1]}"
    
    @property
    def timepoints(self) -> list:
        """ Returns true if the tree has timepoints """

        if not self.phylotree:
            self.load_file()

        return self.phylotree.timepoints

    def lineage_counts(self, *, include_total: bool=False) -> dict:
        """ Return the counts of each lineage in the tree """

        lineages: dict = {}

        lineage_counts: dict = tree_lineage_counts(tree=self.svg_file_name)

        if self.settings is not None and self.settings.get("lineages"):
            lineage_names = self.settings.get("lineages")
        else:
            return None
        
        if not lineage_names:
            return None

        for color in [color for color in lineage_counts if color != "total"]:
            if color in lineage_names:
                lineages[lineage_names[color]] = lineage_counts[color]
                lineages[lineage_names[color]]["color"] = color

            else:
                return None
            
        if include_total:
            lineages["total"] = lineage_counts["total"]

        return lineages
    
    def get_sequence_names(self) -> dict:
        """ Returns a dictionary of sequences for the tree """

        return tree_sequence_names(self.svg_file_name)

    def get_sequence_names_by_color(self, color: str, all_sequence_names: dict=None) -> list:
        """ Returns a list of sequences for the given color """

        if not all_sequence_names:
            all_sequence_names: dict = self.get_sequence_names()

        color_sequence_names: list = [sequence["name"] for sequence in all_sequence_names if sequence["color"] == color]

        return color_sequence_names

    def extract_lineage(self, *, color: str, name: str, sequences: dict=None, all_sequence_names: dict=None, sort: str=None) -> list[dict[str: str]]:
        """ Returns the lineage object for the given color """

        lineage: list[dict[str: str]] = []
        sequence_names: list = []

        if not all_sequence_names:
            all_sequence_names: dict = tree_sequence_names(self.svg_file_name)
        
        if not sequences:
            sequences = SeqIO.index(self.fasta_file_name, "fasta")

        if not sort or sort == "tree":
            sequence_names = [name for name in self.ordered_sequence_names() if name in self.get_sequence_names_by_color(color=color, all_sequence_names=all_sequence_names)]

        elif sort == "timepoint_frequency":
            timepoint_counts: dict[str: dict[str:list]] = {}

            for timepoint in self.timepoints:
                timepoint_counts[timepoint] = {}

                for sequence_name in self.get_sequence_names_by_color(color=color, all_sequence_names=all_sequence_names):
                    if timepoint != sequence_name.split("_")[2]:
                        continue

                    count: int = int(sequence_name.split("_")[-1])

                    if count not in timepoint_counts[timepoint]:
                        timepoint_counts[timepoint][count] = []

                    timepoint_counts[timepoint][count].append(sequence_name)

            for timepoint in timepoint_counts:
                if timepoint not in timepoint_counts or not timepoint_counts[timepoint]:
                    continue

                count = sorted(timepoint_counts[timepoint].keys(), reverse=True)[0]
                sequence_names.append(timepoint_counts[timepoint][count][0])
                timepoint_counts[timepoint][count].pop(0)

            for timepoint in timepoint_counts:
                for count in sorted(timepoint_counts[timepoint].keys(), reverse=True):
                    if timepoint_counts[timepoint][count]:
                        sequence_names = sequence_names + timepoint_counts[timepoint][count]

        elif sort == "frequency":
            counts: dict[int: list] = {}

            # sequence_names_temp = self.ordered_sequence_names()
            # if not sequence_names_temp:
            #     sequence_names_temp = self.get_sequence_names_by_color(color=color, all_sequence_names=all_sequence_names)

            for sequence_name in self.get_sequence_names_by_color(color=color, all_sequence_names=all_sequence_names):
                count: int = int(sequence_name.split("_")[-1])
                
                if count not in counts:
                    counts[count] = []
                counts[count].append(sequence_name)

            for count in sorted(counts.keys(), reverse=True):
                if counts[count]:
                    sequence_names = sequence_names + counts[count]

        if not sequence_names:
            sequence_names = self.get_sequence_names_by_color(color=color, all_sequence_names=all_sequence_names)

        for sequence_name in sequence_names:
            lineage.append({"name": sequence_name, "sequence": sequences.get_raw(sequence_name).decode()})

        return lineage
    
    def extract_lineage_to_fasta(self, *, color: str, name: str, sequences: dict=None, all_sequence_names: dict=None, sort: str=None) -> str:
        """ Returns a .fasta file as a string for the given color """

        fasta: str = ""

        if not all_sequence_names:
            all_sequence_names: dict = tree_sequence_names(self.svg_file_name)
        
        if not sequences:
            sequences = SeqIO.index(self.fasta_file_name, "fasta")

        for seqeuence in self.extract_lineage(color=color, name=name, sequences=sequences, all_sequence_names=all_sequence_names, sort=sort):
            fasta += seqeuence['sequence']

        return fasta
    
    def extract_all_lineages_to_fasta(self, sort: str = None) -> dict:

        fastas: dict = {}

        all_sequence_names: dict = tree_sequence_names(self.svg_file_name)
        sequences = SeqIO.index(self.fasta_file_name, "fasta")

        lineage_counts = self.lineage_counts()

        for lineage_name in lineage_counts:
            color = lineage_counts[lineage_name]["color"]
            fastas[lineage_name] = self.extract_lineage_to_fasta(color=color, name=lineage_name, sequences=sequences, all_sequence_names=all_sequence_names, sort=sort)

        return fastas

    def extract_all_lineages_to_zip(self) -> bytes:
        """ Returns a zip file of all the lineages in the tree """

        mem_zip = io.BytesIO()
        lineages = self.extract_all_lineages_to_fasta()

        with zipfile.ZipFile(mem_zip, mode="w",compression=zipfile.ZIP_DEFLATED) as zipped_lineages:
            for lineage_name, lineage in self.extract_all_lineages_to_fasta(sort="tree").items():
                zipped_lineages.writestr(os.path.join(f"{self.name}_sorted_by_tree_position", f"{self.name}_{lineage_name}.fasta"), lineage)

            for lineage_name, lineage in self.extract_all_lineages_to_fasta(sort="timepoint_frequency").items():
                zipped_lineages.writestr(os.path.join(f"{self.name}_sorted_by_frequency", f"{self.name}_{lineage_name}.fasta"), lineage)

            zipped_lineages.writestr(f"{self.name}_lineage_summary.csv", self.lineage_info_csv())

        return mem_zip.getvalue()
    
    def lineage_info_csv(self) -> str:
        """ Get all the lineage info as a csv """

        csv: list[list[str]] = [[]]
        csv_collector: str = ""

        ordering: dict[str: list] = get_lineage_dict(ordering="only")
        lineage_counts: dict = self.lineage_counts(include_total=True)

        sample_base: str = self.sample_name
        timepoints: list = [timepoint for timepoint in sorted(lineage_counts["total"]["timepoints"].keys())]

        if timepoints:
            csv[0].append("Sample")
            csv.append([f"{sample_base}_{'-'.join(timepoints)}"])

            csv[0].append("Sequences")
            csv[1].append(lineage_counts["total"]["count"])

            for name in ordering["Ordering"]:
                csv[0].append(name)
                csv[0].append(f"{name} freq")

                if name in lineage_counts:
                    csv[1].append(lineage_counts[name]["total"])
                    csv[1].append(round((lineage_counts[name]["total"]/lineage_counts["total"]["count"]), 4))
                else:
                    csv[1].append("")
                    csv[1].append("")

            for timepoint in timepoints:
                csv.append([f"{sample_base}_{timepoint}"])
                csv[len(csv)-1].append(lineage_counts["total"]["timepoints"][timepoint])

                for name in ordering["Ordering"]:
                    if name in lineage_counts:
                        csv[len(csv)-1].append(lineage_counts[name]["timepoints"][timepoint])
                        csv[len(csv)-1].append(round((lineage_counts[name]["timepoints"][timepoint]/lineage_counts["total"]["timepoints"][timepoint]), 4))
                    else:
                        csv[len(csv)-1].append("")
                        csv[len(csv)-1].append("")
        else:
            csv[0].append("Sample")
            csv.append([sample_base])

            csv[0].append("Sequences")
            csv[1].append(lineage_counts["total"]["count"])

            for name in ordering["Ordering"]:
                csv[0].append(name)
                csv[0].append(f"{name} freq")

                if name in lineage_counts:
                    csv[1].append(lineage_counts[name]["count"])
                    csv[1].append(round((lineage_counts[name]["count"]/lineage_counts["total"]["count"]), 4))
                else:
                    csv[1].append("")
                    csv[1].append("")

        for row in csv:
            for col in row:
                csv_collector += f"{col},"
            csv_collector += "\n"

        return csv_collector
    
    def load_file(self) -> None:
        """ Loads the file for the tree """

        if self.phylotree:
            self.phylotree.load_file()
        else:
            self.phylotree = PhyloTree(file_name=self.svg_file_name)

    def swap_by_counts(self) -> Union[None, str]:
        """ Swap lineages that have lower counts than lineages later in the list """

        if not self.phylotree:
            self.phylotree.load_file()
        
        return self.phylotree.swap_by_counts()

    def save_file(self) -> None:
        """ Saves the file for the tree """

        date_tag: str = datetime.datetime.now().strftime("%m.%d.%y_%H.%M")
        shutil.copyfile(self.svg_file_name, f"{self.svg_file_name}.{date_tag}")

        if self.phylotree:
            self.phylotree.save()

    def ordered_sequence_names(self) -> list:
        """ Get sequence names in order of the tree """

        ordered_sequence_names: list = []

        try:
            with open(self.fasta_file_name) as fasta_file:
                for line in fasta_file:
                    if line.startswith(">"):
                        ordered_sequence_names.append(line[1:].strip())
        except:
            return None
        
        return ordered_sequence_names
        

# Importing last to avoid circular imports
from phylobook.projects.utils import svg_file_name, fasta_file_name, tree_lineage_counts, tree_sequence_names, PhyloTree, get_lineage_dict
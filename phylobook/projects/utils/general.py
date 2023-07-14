import logging
log = logging.getLogger('app')

import os, glob

from django.conf import settings

import xml.etree.ElementTree as ET

from phylobook.projects.models import Tree, Project, Lineage


def fasta_type(*, tree: Tree) -> str:
    """ Returns either 'NT' (nucleotide) or 'AA' (amino acid) """

    nt_codes: str = "ACGTUiRYKMSWBDHVN-" # IUPAC nucleotide codes

    file_names = glob.glob(os.path.join(settings.PROJECT_PATH, tree.project.name, tree.name + "*.fasta"))
    if not len(file_names):
        return fasta_type_by_file_name(tree=tree)
    
    with open(file_names[0], 'r') as file:
        for line in file:
            if line.startswith(">"):
                continue
            else:
                for symbol in line.strip():
                    if symbol.upper() not in nt_codes:
                        return "AA"
    return "NT"


def fasta_type_by_file_name(*, tree: Tree) -> str:
    """ Returns either 'NT' (nucleotide) or 'AA' (amino acid), determined by file name or 'Unknown' if it can't be determined """

    aa_tags = ["AA","Gag", "Env","Pol"]
    nt_tags = ["NT", "GP", "POL", "REN", "gag", "env", "pol"]

    for tag in aa_tags:
        if tag in tree.name.split("_"):
            return "AA"

    for tag in nt_tags:
        if tag in tree.name.split("_"):
            return "NT"

    return "Unknown"


def svg_file_name(*, tree: Tree, project: Project) -> str:
    """ Returns the name of the tree file
    It's found this way because there can be variations in the file name """

    highlighter_png: str = glob.glob(os.path.join(settings.PROJECT_PATH, project.name, f"{tree.name}*_highlighter.png"))[0]
    svg_base: str = highlighter_png.replace("_highlighter.png", "")
    svg: str = glob.glob(os.path.join(settings.PROJECT_PATH, project.name, f"{svg_base}*.svg"))[0]

    return svg


def fasta_file_name(*, tree: Tree, project: Project) -> str:
    """ Returns the name of the tree file
    It's found this way because there can be variations in the file name """

    highlighter_png: str = glob.glob(os.path.join(settings.PROJECT_PATH, project.name, f"{tree.name}*_highlighter.png"))[0]
    file_base: str = highlighter_png.replace("_highlighter.png", "")
    fasta: str = glob.glob(os.path.join(settings.PROJECT_PATH, project.name, f"{file_base}*_highlighter.fasta"))

    if len(fasta):
        return fasta[0]
    
    fasta: str = glob.glob(os.path.join(settings.PROJECT_PATH, project.name, f"{file_base}*.fasta"))
    if len(fasta):
        return fasta[0]
    
    fasta: str = glob.glob(os.path.join(settings.PROJECT_PATH, project.name, f"{project.name}*.fasta"))
    if len(fasta):
        return fasta[0]
    
    return None


def get_lineage_dict() -> dict[str: list]:
    """ Returns a list of all lineages in the DB """

    lineage_dict: dict[str: list] = {}

    for lineage in Lineage.objects.all():
        if lineage.color not in lineage_dict:
            lineage_dict[lineage.color] = []

        lineage_dict[lineage.color].append(lineage.lineage_name)

    return lineage_dict
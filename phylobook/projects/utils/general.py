import logging
log = logging.getLogger('app')

import os, glob, hashlib

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

    # highlighter_png: str = glob.glob(os.path.join(settings.PROJECT_PATH, project.name, f"{tree.name}*_highlighter.png"))[0]
    # svg_base: str = highlighter_png.replace("_highlighter.png", "")
    # svg_list = glob.glob(os.path.join(settings.PROJECT_PATH, project.name, f"{svg_base}*.svg"))

    svg_list = glob.glob(os.path.join(settings.PROJECT_PATH, project.name, f"{tree.name}*.svg"))

    if svg_list:
        svg: str = svg_list[0]
    else:
        svg = None

    return svg


def fasta_file_name(*, tree: Tree, project: Project, prefer_origional: bool=False) -> str:
    """ Returns the name of the tree file
    It's found this way because there can be variations in the file name """

    # highlighter_png: str = glob.glob(os.path.join(settings.PROJECT_PATH, project.name, f"{tree.name}*_highlighter.png"))[0]
    # file_base: str = highlighter_png.replace("_highlighter.png", "")
    # fasta: str = glob.glob(os.path.join(settings.PROJECT_PATH, project.name, f"{file_base}*_highlighter.fasta"))

    # if len(fasta):
    #     return fasta[0]
    
    # fasta: str = glob.glob(os.path.join(settings.PROJECT_PATH, project.name, f"{file_base}*.fasta"))
    # if len(fasta):
    #     return fasta[0]
    
    # fasta: str = glob.glob(os.path.join(settings.PROJECT_PATH, project.name, f"{project.name}*.fasta"))
    # if len(fasta):
    #     return fasta[0]
    
    # return None

    fasta: str = None
    fasta_list = glob.glob(os.path.join(settings.PROJECT_PATH, project.name, f"{tree.name}*.fasta"))

    if fasta_list:
        if len(fasta_list) == 1:
            fasta: str = fasta_list[0]
        else:
            match_fasta: bool = False if prefer_origional else True

            while len(fasta_list) > 1:   
                test_fasta = fasta_list.pop()
                if test_fasta.endswith("_highlighter.fasta") == match_fasta:
                    fasta = test_fasta
                    break
            else:
                fasta = fasta_list[0]

    return fasta


def nexus_file_name(*, tree: Tree, project: Project) -> str:
    """ Returns the name of a nexus tree file """

    tre_list = glob.glob(os.path.join(settings.PROJECT_PATH, project.name, f"{tree.name}*nexus.tre"))

    if tre_list:
        tre: str = tre_list[0]
    else:
        tre: str = None

    return tre


def get_lineage_dict(ordering: str=None) -> dict[str: list]:
    """ Returns a list of all lineages in the DB """

    lineage_dict: dict[str: list] = {}

    if ordering == "include":
        lineage_queryset = Lineage.objects.all()
    if ordering == "only":
        lineage_queryset = Lineage.objects.filter(color="Ordering")
    elif not ordering or ordering == "exclude":
        lineage_queryset = Lineage.objects.exclude(color="Ordering")

    for lineage in lineage_queryset:
        if lineage.color not in lineage_dict:
            lineage_dict[lineage.color] = []

        lineage_dict[lineage.color].append(lineage.lineage_name)

    return lineage_dict


def color_hex_to_rgb(hex_value: str) -> tuple[int, int, int]:
    """ Convert a hex color to rgb  """

    if type(hex_value) is not str:
        raise TypeError("hex must be a string")
    
    if hex_value.startswith("#"):
        hex_value = hex_value.lstrip('#')

    if len(hex_value) != 6:
        raise ValueError("hex must be a 6 digit hex value")

    hex_value = hex_value.lstrip('#')
    return tuple(int(hex_value[i:i+2], 16) for i in (0, 2, 4))


def color_hex_to_rgb_string(hex_value: str) -> str:
    """ Convert a hex color to rgb string """

    rgb: tuple[int, int, int] = color_hex_to_rgb(hex_value=hex_value)
    return f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"


def file_hash(*, file_name: str) -> str:
    """ Returns the hash of a file 
    https://stackoverflow.com/questions/3431825/generating-an-md5-checksum-of-a-file"""

    import hashlib

    hash_md5 = hashlib.md5()
    with open(file_name, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    
    return hash_md5.hexdigest()


def color_by_short(color: str) -> dict[str: str]:
    """ Returns the color dict for a given short color name """

    color_object = [color_object for color_object in settings.ANNOTATION_COLORS if color_object["short"] == color]

    if not len(color_object):
        raise ValueError(f"Color {color} not found in settings.ANNOTATION_COLORS")
    
    return color_object[0]
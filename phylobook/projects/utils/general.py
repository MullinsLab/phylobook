import logging
log = logging.getLogger('app')

import os, glob, hashlib

from django.conf import settings

from Bio.Align import MultipleSeqAlignment
import xml.etree.ElementTree as ET

from phylobook.projects.models import Tree, Project, Lineage


def svg_dimensions(svg_file_name: str) -> tuple[int, int]:
    """ Returns the dimensions of an svg file as a tuple of (width, height) """

    tree_svg = ET.parse(svg_file_name)
    root = tree_svg.getroot()
    view_box = root.attrib["viewBox"]
    _, _, width, height = view_box.split(" ")

    return (int(float(width)), int(float(height)))


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

    svg_list = glob.glob(os.path.join(settings.PROJECT_PATH, project.name, f"{tree.name}*.svg"))

    new_svg_list: list = []

    for test_svg in svg_list:
        if "_highlighter" not in test_svg and "_match" not in test_svg:
            new_svg_list.append(test_svg)

    if new_svg_list:
        svg: str = new_svg_list[0]
    else:
        svg = None

    return svg


def fasta_file_name(*, tree: Tree, project: Project, prefer_original: bool=False) -> str:
    """ Returns the name of the tree file
    It's found this way because there can be variations in the file name """

    fasta: str = None
    fasta_list = glob.glob(os.path.join(settings.PROJECT_PATH, project.name, f"{tree.name}*.fasta"))

    if fasta_list:
        while len(fasta_list) > 1:   
            test_fasta = fasta_list.pop()
            if prefer_original and "collapsed" in test_fasta:
                fasta = test_fasta
                break

            elif test_fasta.endswith("_highlighter.fasta") and not prefer_original:
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

def newick_file_name(*, tree: Tree, project: Project) -> str:
    """ Returns the name of a nexus tree file """

    tre_list = glob.glob(os.path.join(settings.PROJECT_PATH, project.name, f"{tree.name}*newick.tre"))

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


class SequenceNameShortenizer(object):
    """ Class to shorten sequence names """

    def __init__(self, alignment: MultipleSeqAlignment):
        """ Set upt the shortenizer """

        self.alignment = alignment
        self.setup_tags()

    def setup_tags(self):
        """ Setup the tags """
        
        self.used_tags: list = []
        
        tags: dict[int: str] = {}
        tag_count: int = None

        for sequence in self.alignment:
            for index, tag in enumerate(sequence.id.split("_")):

                if tag_count is None:
                    tag_count = len(sequence.id.split("_"))
                elif tag_count != len(sequence.id.split("_")):
                    raise ValueError("All sequences must have the same number of tags")

                if index in self.used_tags:
                    continue

                if index not in tags:
                    tags[index] = tag
                
                elif tag != tags[index]:
                    self.used_tags.append(index)

    def shortenize(self, sequence_name: str) -> str:
        """ Shortenize a record """

        tags = sequence_name.split("_")
        new_tags = []

        for index in sorted(self.used_tags):
            new_tags.append(tags[index])

        return "_".join(new_tags)
                


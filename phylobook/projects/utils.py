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


def tree_sequence_names(tree_file: str) -> list[dict[str: str]]:
    """ Get all the sequence names from the a specific tree """

    if not tree_file:
        return None

    root = ET.parse(tree_file).getroot()
    sequences: list[dict[str: str]] = []

    for sequence in root.iter("{http://www.w3.org/2000/svg}text"):
        if "class" not in sequence.attrib or not sequence.attrib["class"] or not sequence.attrib["class"].startswith("box"):
            continue
        
        sequences.append({"name": sequence.text, "color": sequence.attrib["class"].replace("box", "")})

    return sequences


def parse_sequence_name(sequence_name: str) -> dict:
    """ Get the timepoint and mulitplicity from a sequence name """

    if not sequence_name:
        return None

    sequence: dict = {}
    sequence_bits: list = sequence_name.split("_")

    if len(sequence_bits) >= 4 and sequence_bits[2].isnumeric():
        sequence["timepoint"] = int(sequence_bits[2])
    else:
        sequence["timepoint"] = None

    if sequence_bits[-1].isnumeric():    
        sequence["multiplicity"] = int(sequence_bits[-1])
    else:
        return None

    return sequence


def parse_sequences(sequences: list[dict[str: str]]) -> list[dict[str: str]]:
    """ Returns True if the tree has timepoints """

    if not sequences:
        return [], False

    sequences_out: list[dict[str: str]] = []
    has_timepoints: bool = False

    for sequence in sequences:
        sequences_out.append(sequence | parse_sequence_name(sequence["name"]))

    if [sequence for sequence in sequences_out if sequence["timepoint"] is not None]:
        has_timepoints = True

    return sequences_out, has_timepoints


def tree_lineage_counts(tree_file: str) -> dict[str: dict]:
    """ Get all the lineage counts from a specific tree """

    if not tree_file:
        return None
    
    sequences, has_timepoints = parse_sequences(tree_sequence_names(tree_file))

    lineage_counts: dict[str: dict] = {}
    count_collector: int = 0

    for sequence in sequences:
        if not sequence:
            return None
        
        if has_timepoints:
            if sequence["color"] not in lineage_counts:
                lineage_counts[sequence["color"]] = {"timepoints": {}}

            if sequence["timepoint"] not in lineage_counts[sequence["color"]]["timepoints"]:
                lineage_counts[sequence["color"]]["timepoints"][sequence["timepoint"]] = 0

            lineage_counts[sequence["color"]]["timepoints"][sequence["timepoint"]] += sequence["multiplicity"]
            count_collector += sequence["multiplicity"]
            # log.debug(f"Color:, {sequence['color']}, timepoint: {sequence['timepoint']}, count: {sequence['multiplicity']}, subtotal: {lineage_counts[sequence['color']]['timepoints'][sequence['timepoint']]}, total: {count_collector}")
        
        else:
            if sequence["color"] not in lineage_counts:
                lineage_counts[sequence["color"]] = {"count": 0}

            lineage_counts[sequence["color"]]["count"] += sequence["multiplicity"]
            count_collector += sequence["multiplicity"]

    lineage_counts["total"] = count_collector

    return lineage_counts


def get_lineage_dict() -> dict[str: list]:
    """ Returns a list of all lineages in the DB """

    lineage_dict: dict[str: list] = {}

    for lineage in Lineage.objects.all():
        if lineage.color not in lineage_dict:
            lineage_dict[lineage.color] = []

        lineage_dict[lineage.color].append(lineage.lineage_name)

    return lineage_dict
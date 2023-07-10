import os, glob

from django.conf import settings

import xml.etree.ElementTree as ET

from phylobook.projects.models import Tree


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
                        print(symbol.upper())
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


def tree_sequences(tree_file: str) -> list[dict[str: str]]:
    """ Get all the sequence names from the a specific tree """

    if not tree_file:
        return None

    root = ET.parse(tree_file).getroot()
    sequences: list[dict[str: str]] = []

    for sequence in root.iter("{http://www.w3.org/2000/svg}text"):
        if "class" not in sequence.attrib:
            continue

        # print(f"\n\n{sequence.text}\n\n")
        sequences.append({"name": sequence.text, "color": sequence.attrib["class"].replace("box", "")})

    return sequences


def parse_sequence_name(sequence_name: str) -> dict:
    """ Get the timepoint and mulitplicity from a sequence name """

    if not sequence_name:
        return None

    sequence: dict = {}
    sequence_bits: list = sequence_name.split("_")

    if sequence_bits[2].isnumeric():
        sequence["timepoint"] = int(sequence_bits[2])
    else:
        return None

    if sequence_bits[-1].isnumeric():    
        sequence["multiplicity"] = int(sequence_bits[-1])
    else:
        return None

    return sequence


def tree_lineage_counts(tree_file: str) -> dict[str: dict]:
    """ Get all the lineage counts from a specific tree """

    if not tree_file:
        return None
    
    sequences = tree_sequences(tree_file)
    lineage_counts: dict[str: dict] = {}

    for sequence in sequences:
        attributes = parse_sequence_name(sequence["name"])
        
        if not attributes:
            return None
        
        if sequence["color"] not in lineage_counts or attributes["timepoint"] < lineage_counts[sequence["color"]]["timepoint"]:
            lineage_counts[sequence["color"]] = {
                "count": attributes["multiplicity"], 
                "timepoint": attributes["timepoint"]
            }

        elif attributes["timepoint"] == lineage_counts[sequence["color"]]["timepoint"]:
            lineage_counts[sequence["color"]]["count"] += attributes["multiplicity"]

    return lineage_counts
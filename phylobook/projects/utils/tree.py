import logging
log = logging.getLogger('app')

import os, glob

from django.conf import settings

import xml.etree.ElementTree as ET

from phylobook.projects.models import Tree, Project, Lineage

from phylobook.projects.utils.general import fasta_type, fasta_type_by_file_name, svg_file_name


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


def parse_sequences(sequences: list[dict[str: str]]) -> tuple[list[dict[str: str]], tuple[int]]:
    """ Returns True if the tree has timepoints """

    if not sequences:
        return [], False

    sequences_out: list[dict[str: str]] = []

    for sequence in sequences:
        sequences_out.append(sequence | parse_sequence_name(sequence["name"]))

    timepoints: set = {sequence["timepoint"] for sequence in sequences_out if sequence["timepoint"] is not None}

    return sequences_out, tuple(sorted(timepoints))


def tree_lineage_counts(tree_file: str) -> dict[str: dict]:
    """ Get all the lineage counts from a specific tree """

    if not tree_file:
        return None
    
    sequences, timepoints = parse_sequences(tree_sequence_names(tree_file))

    lineage_counts: dict[str: dict] = {
        "total": {
            "count": 0,
            "timepoints": {},
        }
    }

    for sequence in sequences:
        if not sequence:
            return None
        
        if timepoints:
            if sequence["color"] not in lineage_counts:
                lineage_counts[sequence["color"]] = {"timepoints": {timepoint: 0 for timepoint in timepoints}}

            if sequence["timepoint"] not in lineage_counts[sequence["color"]]["timepoints"]:
                lineage_counts[sequence["color"]]["timepoints"][sequence["timepoint"]] = 0
            lineage_counts[sequence["color"]]["timepoints"][sequence["timepoint"]] += sequence["multiplicity"]
            lineage_counts["total"]["count"] += sequence["multiplicity"]

            if sequence["timepoint"] not in lineage_counts["total"]["timepoints"]:
                lineage_counts["total"]["timepoints"][sequence["timepoint"]] = 0
            lineage_counts["total"]["timepoints"][sequence["timepoint"]] += sequence["multiplicity"]
        
        else:
            if sequence["color"] not in lineage_counts:
                lineage_counts[sequence["color"]] = {"count": 0}

            lineage_counts[sequence["color"]]["count"] += sequence["multiplicity"]
            lineage_counts["total"]["count"] += sequence["multiplicity"]

    return lineage_counts
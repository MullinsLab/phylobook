import logging
log = logging.getLogger('app')

import re
import xml.etree.ElementTree as ET
from typing import Union

from django.conf import settings

from phylobook.projects.utils.general import color_hex_to_rgb_string, color_by_short


class PhyloTree(object):
    """ Class to do work with a Phylobook tree """

    def __init__(self, *, file_name: str = None):
        """ Set up the object """

        self.file_name = file_name

        self.sequences: dict[str: dict[str: ET.Element]] = {}
        self.svg = None
        self.root: ET.Element = None

        self.load()
        self._prep_sequences()

    def load(self, *, file_name: str = None):
        """ Load a new tree """

        if file_name:
            self.file_name = file_name

        self.svg = ET.parse(self.file_name)
        self.root = self.svg.getroot()

    def save(self, *, file_name: str = None):
        """ Save the tree """

        if file_name:
            self.file_name = file_name

        self.svg.write(self.file_name)
    
    def change_lineage(self, *, sequence: Union[str, dict]=None, color: str=None) -> None:
        """ Change the lineage of a sequence """

        if isinstance(sequence, str):
            if sequence not in self.sequences:
                raise ValueError(f"Sequence {sequence} not found in tree")
            else:
                sequence_object = self.sequences[sequence]
        elif type(sequence) is dict:
            sequence_object = sequence
        else:
            raise ValueError(f"Sequence must be a string or a dictionary, not {type(sequence)}")

        color_object = color_by_short(color=color)

        sequence_object["text"].attrib["class"] = f"box{color_object['short']}"
        self._set_color_in_box(sequence=sequence_object["name"], hex_value=color_object["value"])
        sequence_object["color"] = color_object["short"]

    def swap_lineages(self, color1: str, color2: str) -> None:
        """ Swap two lineages """

        color1_object = color_by_short(color1)
        color2_object = color_by_short(color2)

        log.debug(self.sequences)

        for sequence in self.sequences.values():
            log.debug(f"Sequence: {sequence}")
            log.debug(f"Short: {color1_object['short']}")
                      
            if sequence["color"] == color1_object["short"]:
                self.change_lineage(sequence=sequence, color=color2_object["short"])
            elif sequence["color"] == color2_object["short"]:
                self.change_lineage(sequence=sequence, color=color1_object["short"])

    def _prep_sequences(self) -> None:
        """ Set up the self.elements dictionarie """

        for text_element in self.root.iter("{http://www.w3.org/2000/svg}text"):
            if text_element.attrib.get("class") and text_element.attrib["class"].startswith("box"):
                if text_element.text not in self.sequences:
                    self.sequences[text_element.text] = {}
                self.sequences[text_element.text]["text"] = text_element
                self.sequences[text_element.text]["color"] = text_element.attrib["class"].replace("box", "")
                self.sequences[text_element.text]["name"] = text_element.text

        for path_element in self.root.iter("{http://www.w3.org/2000/svg}path"):
            if path_element.attrib.get("id"):
                if path_element.attrib["id"] not in self.sequences:
                    self.sequences[path_element.attrib["id"]] = {}
                self.sequences[path_element.attrib["id"]]["box"] = path_element 

    def _set_color_in_box(self, *, sequence: str, hex_value: str) -> str:
        """ Replace the color in a d string """

        element: ET.Element = self.sequences[sequence]["box"]
        style = element.attrib["style"]
        new_rgb = color_hex_to_rgb_string(hex_value=hex_value)

        element.attrib["style"] = re.sub(r"rgb\((.*)\)", new_rgb, style)


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
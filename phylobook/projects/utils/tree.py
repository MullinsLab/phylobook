import logging
log = logging.getLogger('app')

import re
import xml.etree.ElementTree as ET
from typing import Union

from django.conf import settings

from phylobook.projects.utils.general import color_hex_to_rgb_string, color_by_short, remove_string_from_file


class PhyloTree(object):
    """ Class to do work with a Phylobook tree """

    def __init__(self, *, file_name: str = None):
        """ Set up the object """

        self.file_name = file_name

        self.sequences: dict[str: dict[str: ET.Element]] = {}
        self.lineage_counts: dict[str: dict] = {}
        self.timepoints: list[int] = []
        self.svg = None
        self.root: ET.Element = None

        self.load()

        self._prep_sequences()
        self._prep_tree_lineage_counts()

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

        ET.register_namespace("", "http://www.w3.org/2000/svg")
        self.svg.write(self.file_name)
        # remove_string_from_file(file_name=self.file_name, string="ns0:")
    
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

        for sequence in self.sequences.values():
            if sequence["color"] == color1_object["short"]:
                self.change_lineage(sequence=sequence, color=color2_object["short"])
            elif sequence["color"] == color2_object["short"]:
                self.change_lineage(sequence=sequence, color=color1_object["short"])

        self._prep_tree_lineage_counts()

    def swap_by_counts(self) -> Union[None, str]:
        """ Swap lineages that have lower counts than lineages later in the list """

        safety = 0
        colors: list = []

        while swap := self.need_swaps():
            self.swap_lineages(swap[0], swap[1])
            
            if swap[0] not in colors:
                colors.append(swap[0])
            
            if swap[1] not in colors:
                colors.append(swap[1])

            safety += 1
            if safety > 100:
                return "Safety limit reached"
            
        if colors:
            return ', '.join([color_by_short(color)['name'] for color in colors])
        
        return None

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

    def _prep_tree_lineage_counts(self) -> dict[str: dict]:
        """ Get the counts of each lineage in the tree 
        Move this whole thing into the PhyloTree object """

        sequence_list: list[dict[str: str]] = [{"name": sequence, "color": self.sequences[sequence]["color"]} for sequence in self.sequences.keys()]
        sequences, timepoints = parse_sequences(sequence_list)

        self.timepoints = timepoints

        lineage_counts: dict[str: dict] = {
            "total": {
                "count": 0,
                "timepoints": {},
            }
        }

        for sequence in sequences:
            if timepoints:
                if sequence["color"] not in lineage_counts:
                    lineage_counts[sequence["color"]] = {"timepoints": {timepoint: 0 for timepoint in timepoints}, "total": 0}

                if sequence["timepoint"] not in lineage_counts[sequence["color"]]["timepoints"]:
                    lineage_counts[sequence["color"]]["timepoints"][sequence["timepoint"]] = 0

                lineage_counts[sequence["color"]]["timepoints"][sequence["timepoint"]] += sequence["multiplicity"]
                lineage_counts[sequence["color"]]["total"] += sequence["multiplicity"]
                
                lineage_counts["total"]["count"] += sequence["multiplicity"]

                if sequence["timepoint"] not in lineage_counts["total"]["timepoints"]:
                    lineage_counts["total"]["timepoints"][sequence["timepoint"]] = 0
                    
                lineage_counts["total"]["timepoints"][sequence["timepoint"]] += sequence["multiplicity"]
            
            else:
                if sequence["color"] not in lineage_counts:
                    lineage_counts[sequence["color"]] = {"count": 0}

                lineage_counts[sequence["color"]]["count"] += sequence["multiplicity"]
                lineage_counts["total"]["count"] += sequence["multiplicity"]

        self.lineage_counts = lineage_counts

    def need_swaps(self) -> Union[bool, list]:
        """ Returns tuple of swaps to make or None """

        colors = settings.ANNOTATION_COLORS

        for index1 in range(len(colors)-1):
            color1 = colors[index1]
            
            if not color1["swapable"]:
                continue

            for index2 in range(index1+1, len(colors)-1):
                color2 = colors[index2]

                if not color2["swapable"]:
                    continue
                
                if self.timepoints:
                    for timepoint in self.timepoints:
                        if color1["short"] in self.lineage_counts:
                            color1_count: int = self.lineage_counts[color1["short"]]["timepoints"][timepoint]
                        else:
                            color1_count: int = 0

                        if color2["short"] in self.lineage_counts:
                            color2_count: int = self.lineage_counts[color2["short"]]["timepoints"][timepoint]
                        else:
                            color2_count: int = 0

                        if color1_count < color2_count:
                            return (color1["short"], color2["short"])
                        elif color1_count > color2_count:
                            break
                else:
                    if color1["short"] in self.lineage_counts:
                        color1_count: int = self.lineage_counts[color1["short"]]["count"]
                    else:
                        color1_count: int = 0

                    if color2["short"] in self.lineage_counts:
                        color2_count: int = self.lineage_counts[color2["short"]]["count"]
                    else:
                        color2_count: int = 0

                    if color1_count < color2_count:
                        return (color1["short"], color2["short"])
                    
                    elif color1_count > color2_count:
                            break

        return False


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
        sequence["timepoint"] = sequence_bits[2]
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


def tree_lineage_counts(tree: str) -> dict[str: dict]:
    """ Get all the lineage counts from a specific tree """

    if not tree:
        return None
    
    sequences, timepoints = parse_sequences(tree_sequence_names(tree))

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
                lineage_counts[sequence["color"]] = {"timepoints": {timepoint: 0 for timepoint in timepoints}, "total": 0}

            if sequence["timepoint"] not in lineage_counts[sequence["color"]]["timepoints"]:
                lineage_counts[sequence["color"]]["timepoints"][sequence["timepoint"]] = 0

            lineage_counts[sequence["color"]]["timepoints"][sequence["timepoint"]] += sequence["multiplicity"]
            lineage_counts[sequence["color"]]["total"] += sequence["multiplicity"]
            
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
import logging
log = logging.getLogger('test')

import os

from django.test import TestCase, SimpleTestCase

from phylobook.projects import utils 


class TreeTests(TestCase):
    """ Tests that trees can be parsed """

    # Tests for tree_sequences

    def test_tree_sequences_should_return_none_given_none(self):
        """ tree_det_sequence_names should return None when given None """

        self.assertIs(utils.tree_sequence_names(None), None)

    def test_tree_sequences_should_raise_exception_given_nonexistent_file(self):
        """ tree_det_sequence_names should raise an exception when given a nonexistent file """

        with self.assertRaises(FileNotFoundError):
            utils.tree_lineage_counts("bad_name")

    def test_tree_sequences_should_return_list_of_dicts(self):
        """ tree_det_sequence_names should return a list """

        svg_file_name = "/phylobook/test_data/with_timepoints.svg"
        sequences = utils.tree_sequence_names(svg_file_name)

        self.assertIsInstance(sequences, list)
        self.assertIsInstance(sequences[0], dict)

    def test_tree_sequences_should_not_return_empty(self):
        """ tree_get_sequences should not return an empty list """
    
        svg_file_name = "/phylobook/test_data/with_timepoints.svg"
        self.assertGreater(len(utils.tree_sequence_names(svg_file_name)), 0)
    
    def test_tree_sequences_should_contain_particular_sequenc(self):
        """ tree_get_sequences should contain a particular sequence """
    
        svg_file_name = "/phylobook/test_data/with_timepoints.svg"
        sequences = utils.tree_sequence_names(svg_file_name)
        my_sequence = [sequence for sequence in sequences if sequence["name"] == "TP_80_100_1"][0]

        self.assertTrue(my_sequence)
        self.assertEqual(my_sequence["color"], "red")

    # Tests for parse_sequences

    def test_parse_sequences_should_return_dict(self):
        """ parse_sequences should return a dict """

        sequence = utils.parse_sequence_name("V703_0132_200_GP_NT_70_1")
        self.assertIsInstance(sequence, dict)

    def test_parse_sequences_should_not_return_none_when_given_none(self):
        """ parse_sequences should not return None when given None """

        sequence = utils.parse_sequence_name(None)
        self.assertIs(sequence, None)

    def test_parse_sequences_should_return_correct_dict(self):
        """ parse_sequences should return a dict with the correct values """

        sequence = utils.parse_sequence_name("V703_0132_200_GP_NT_70_1")
        self.assertEqual(sequence, {"timepoint": "200", "multiplicity": 1})

    def test_parse_sequences_should_return_none_with_no_multpilicity(self):
        """ parse_sequences should return None with a noncompliant name """

        sequence = utils.parse_sequence_name("V703_0132_200_GP_NT_70_1_test")
        self.assertIs(sequence, None)

    def test_parse_sequences_should_return_value_with_no_timepoint(self):
        """ parse_sequences should return a dict with a no timepoint """

        sequence = utils.parse_sequence_name("V703_test_1")

        self.assertEquals(sequence["multiplicity"], 1)
        self.assertIs(sequence["timepoint"], None)

    # Tests for tree_lineage_counts
    # With test_with_timepoints.svg

    def test_tree_lineage_counts_should_return_dict(self):
        """ tree_lineage_counts should return a dict """

        svg_file_name = "/phylobook/test_data/with_timepoints.svg"
        lineage_counts = utils.tree_lineage_counts(svg_file_name)

        self.assertIsInstance(lineage_counts, dict)

    def test_tree_lineage_counts_should_not_return_empty(self):
        """ tree_lineage_counts should not return an empty list """

        svg_file_name = "/phylobook/test_data/with_timepoints.svg"
        self.assertGreater(len(utils.tree_lineage_counts(svg_file_name)), 0)

    def test_tree_lineage_counts_should_return_none_given_none(self):
        """ tree_lineage_counts should return None when given None """

        self.assertIs(utils.tree_lineage_counts(None), None)

    def test_tree_lineage_counts_should_raise_error_given_bad_file_name(self):
        """ tree_lineage_counts should raise an error when given a bad file name """

        with self.assertRaises(FileNotFoundError):
            utils.tree_lineage_counts("bad_name")

    def test_tree_lineage_counts_should_return_counts_for_colors(self):
        """ tree_lineage_counts should return counts for colors """

        svg_file_name = "/phylobook/test_data/with_timepoints.svg"
        lineage_counts = utils.tree_lineage_counts(svg_file_name)

        self.assertGreater(lineage_counts["red"]["timepoints"]["100"], 0)
    
    def test_tree_lineage_counts_should_be_less_than_total_count(self):
        """ tree_lineage_counts should be less than the total count """

        svg_file_name = "/phylobook/test_data/with_timepoints.svg"
        lineage_counts = utils.tree_lineage_counts(svg_file_name)

        self.assertLess(lineage_counts["red"]["timepoints"]["100"], 184)

    def test_tree_lineage_counts_should_be_178_for_red(self):
        """ tree_lineage_counts should be 178 for red """

        svg_file_name = "/phylobook/test_data/with_timepoints.svg"
        lineage_counts = utils.tree_lineage_counts(svg_file_name)

        self.assertEqual(lineage_counts["red"]["timepoints"]["100"], 38)

    # With test_with_timepoints.svg

    def test_tree_lineage_counts_should_return_counts_for_no_timepoints(self):
        """ tree_lineage_counts should return counts for colors """

        svg_file_name = "/phylobook/test_data/without_timepoints.svg"
        lineage_counts = utils.tree_lineage_counts(svg_file_name)

        self.assertGreater(lineage_counts["red"]["count"], 0)

    def test_tree_lineage_counts_should_be_37_for_red(self):
        """ tree_lineage_counts should be 37 for red """

        svg_file_name = "/phylobook/test_data/without_timepoints.svg"
        lineage_counts = utils.tree_lineage_counts(svg_file_name)

        self.assertEqual(lineage_counts["red"]["count"], 77)

    # Tests for lineage_dict

    def test_lineage_dict_should_return_dictionary(self):
        """ lineage_dict should return a dictionary """

        self.assertIsInstance(utils.get_lineage_dict(), dict)

    def test_lineage_dict_should_return_red_names_correctly(self):
        """ lineage_dict should return a dictionary with correct red names """

        lineage_dict: dict = utils.get_lineage_dict()
        self.assertEqual(lineage_dict["Red"], ['SxL', 'MxL1'])

    def test_lineage_dict_should_include_ordering_given_ordering_include(self):
        """ lineage_dict should include ordering given ordering include """

        lineage_dict: dict = utils.get_lineage_dict(ordering="include")
        self.assertIn("Red", lineage_dict)
        self.assertIn("Ordering", lineage_dict)

    def test_lineage_dict_should_not_includ_ordering_given_no_ordering(self):
        """ lineage_dict should not include ordering given no ordering """

        lineage_dict: dict = utils.get_lineage_dict()
        self.assertIn("Red", lineage_dict)
        self.assertNotIn("Ordering", lineage_dict)

    def test_lineage_dict_should_only_include_ordering_given_ordering_only(self):
        """ lineage_dict should only include ordering given ordering only """

        lineage_dict: dict = utils.get_lineage_dict(ordering="only")
        self.assertIn("Ordering", lineage_dict)
        self.assertNotIn("Red", lineage_dict)

    # Tests for general functions

    def test_color_hex_to_rbg_should_return_tuple(self):
        """ color_hex_to_rgb should return a tuple """

        self.assertIsInstance(utils.color_hex_to_rgb("#00CB85"), tuple)

    def test_color_hex_to_rgp_should_throw_error_given_bad_hex(self):
        """ color_hex_to_rgb should throw an error given a bad hex """

        with self.assertRaises(ValueError):
            utils.color_hex_to_rgb("bad_hex")

        with self.assertRaises(TypeError):
            utils.color_hex_to_rgb(None)

        with self.assertRaises(ValueError):
            utils.color_hex_to_rgb("a")

        with self.assertRaises(ValueError):
            utils.color_hex_to_rgb("aaaaaaaaaaaaaaa")

    def test_color_hex_to_rgb_should_return_correct_tuple(self):
        """ color_hex_to_rgb should return the correct tuple """

        self.assertEqual(utils.color_hex_to_rgb("#00CB85"), (0, 203, 133))
        self.assertEqual(utils.color_hex_to_rgb("00CB85"), (0, 203, 133))
        self.assertEqual(utils.color_hex_to_rgb("#537EFF"), (83, 126, 255))
        self.assertEqual(utils.color_hex_to_rgb("537EFF"), (83, 126, 255))

    # Test for file hash

    def test_file_hash_should_return_correct_hash(self):
        """ file_hash should return the correct hash """

        self.assertEqual(utils.file_hash(file_name="/phylobook/test_data/with_timepoints.svg"), "e63b2204c92284a1eb7e4ccd385265cf")

    # Test for color_by_short

    def test_color_by_short_should_raise_errror_with_bad_color(self):
        """ color_by_short should raise an error with a bad color """

        with self.assertRaises(ValueError):
            utils.color_by_short("bad_color")

    def test_color_by_short_returns_correct_dict(self):
        """ color_by_short should return the correct dictionary """

        self.assertEqual(utils.color_by_short("red"), {'name': 'Red', 'short': 'red', 'swapable': True, 'value': 'FF0000', "has_UOLs": False})


class PhyloTreeTests(SimpleTestCase):
    """ Tests for the PhyloTree class"""

    @classmethod
    def setUp(self):
        """ Set up whatever objects are going to be needed for all tests """

        self.phylotree = utils.PhyloTree(file_name="/phylobook/test_data/with_timepoints.svg")

    def test_phylotree_should_instantiate(self):
        """ PhyloTree should instantiate """

        self.assertIsInstance(self.phylotree, utils.PhyloTree)

    def test_phylotree_should_have_a_non_empty_elements_dict(self):
        """ PhyloTree should have a non-empty elements dict """

        self.assertGreater(len(self.phylotree.sequences), 0)

    def test_phylotree_elememts_should_contain_TP_2_101_16(self):
        """ PhyloTree elements should contain TP_2_101_16 """

        self.assertIn("TP_2_101_16", self.phylotree.sequences)

    def test_phylotree_elements_TP_2_101_16_should_contain_text_element(self):
        """ PhyloTree elements TP_2_101_16 should contain a text element """

        self.assertIn("text", self.phylotree.sequences["TP_2_101_16"])

    def test_phylotree_elements_TP_2_101_16_should_contain_box_element(self):
        """ PhyloTree elements TP_2_101_16 should contain a box element """

        self.assertIn("box", self.phylotree.sequences["TP_2_101_16"])

    def test_phylobtree_lineage_counts_returns_correct_counts(self):
        """ PhyloTree lineage counts returns correct counts """

        self.assertEqual(self.phylotree.lineage_counts["red"], {'timepoints': {"100": 38, "101": 32, "102": 0, "103": 0, "104": 0}, 'total': 70})
        self.assertEqual(self.phylotree.lineage_counts["neonblue"], {'timepoints': {"100": 0, "101": 7, "102": 10, "103": 8, "104": 1}, 'total': 26})

    def test_phylotree_change_lineage_raises_exception_given_bad_sequence_or_color(self):
        """ PhyloTree change lineage raises exception given bad lineage """

        with self.assertRaises(ValueError):
            self.phylotree.change_lineage(sequence="TP_2_101_16_bad", color="neonblue")

        with self.assertRaises(ValueError):
            self.phylotree.change_lineage(sequence="TP_2_101_16", color="bad_color")

    def test_phylotree_change_lineage_doesnt_raise_exception_given_good_sequence_and_color(self):
        """ PhyloTree change lineage doesn't raise exception given good lineage """

        try:
            self.phylotree.change_lineage(sequence="TP_2_101_16", color="neonblue")
        except ValueError:
            self.fail("PhyloTree change lineage raised exception given good lineage")

    def test_phylotree_change_lineage_changes_color(self):
        """ PhyloTree change lineage changes color """

        self.phylotree.change_lineage(sequence="TP_2_101_16", color="neonblue")
        self.assertEqual(self.phylotree.sequences["TP_2_101_16"]["text"].attrib["class"], "boxneonblue")
        self.assertEqual(self.phylotree.sequences["TP_2_101_16"]["box"].attrib["style"], "stroke-width: 1; stroke: rgb(83,126,255); fill: none;")
        self.assertEqual(self.phylotree.sequences["TP_2_101_16"]["color"], "neonblue")

        self.phylotree.save(file_name="/phylobook/test_data/with_timepoints_changed.svg")
        self.assertEqual(utils.file_hash(file_name="/phylobook/test_data/with_timepoints_changed.svg"), "ea9bb2da5eaaf4ff4292a7bcfeda7681")
        os.remove("/phylobook/test_data/with_timepoints_changed.svg")
    
    def test_phylotree_swap_lineages_raises_exception_given_bad_color(self):
        """ PhyloTree swap lineages raises exception given bad color """

        with self.assertRaises(ValueError):
            self.phylotree.swap_lineages("neonblue", "bad_color")

        with self.assertRaises(ValueError):
            self.phylotree.swap_lineages("bad_color", "red")

    def test_phylotree_swap_lineages_changes_TP_2_101_16(self):
        """ PhyloTree swap lineages changes TP_2_101_16 """

        self.phylotree.swap_lineages("neonblue", "red")
        self.assertEqual(self.phylotree.sequences["TP_2_101_16"]["color"], "neonblue")

        self.assertEqual(self.phylotree.lineage_counts["neonblue"], {'timepoints': {'100': 38, '101': 32, '102': 0, '103': 0, '104': 0}, 'total': 70})
        self.assertEqual(self.phylotree.lineage_counts["red"], {'timepoints': {"100": 0, "101": 7, "102": 10, "103": 8, "104": 1}, 'total': 26})

        self.phylotree.save(file_name="/phylobook/test_data/with_timepoints_changed.svg")
        self.assertEqual(utils.file_hash(file_name="/phylobook/test_data/with_timepoints_changed.svg"), "3a1b67a4bf3c88cdf6bd34e96dad2f4f")
        os.remove("/phylobook/test_data/with_timepoints_changed.svg")

    def test_phylotree_should_swap_returns_none_if_no_swap_needed(self):
        """ PhyloTree should swap returns None if no swap needed """

        self.assertFalse(self.phylotree.need_swaps())

    def test_phylotree_should_swap_return_tuple_of_swaps_if_swap_needed(self):
        """ PhyloTree should swap return tuple of swaps if swap needed """

        self.phylotree.swap_lineages("neonblue", "red")

        self.assertEqual(self.phylotree.need_swaps(), ("red", "neonblue"))

    def test_phylotree_swap_by_counts_returns_none_if_no_swap_needed(self):
        """ PhyloTree swap_by_counts returns None if no swap needed """

        self.assertFalse(self.phylotree.swap_by_counts())

    def test_phylotree_swap_by_counts_returns_string_if_swaps_performed(self):
        """ PhyloTree swap_by_counts returns string if swaps were performed """

        self.phylotree.swap_lineages("neonblue", "red")

        self.assertEqual(self.phylotree.swap_by_counts(), "Red, Neon Blue")

        self.assertEqual(self.phylotree.lineage_counts["red"], {'timepoints': {"100": 38, "101": 32, "102": 0, "103": 0, "104": 0}, 'total': 70})
        self.assertEqual(self.phylotree.lineage_counts["neonblue"], {'timepoints': {"100": 0, "101": 7, "102": 10, "103": 8, "104": 1}, 'total': 26})

    def test_phylotree_swap_by_counts_correct_for_timepoints_misordered(self):
        """ PhyloTree swap_by_counts correct for timepoints misordered """

        self.assertEqual(utils.file_hash(file_name="/phylobook/test_data/with_timepoints_misordered.svg"), "e99dd0323b06120f30f1eba5c8da19ec")
        
        phylotree=utils.PhyloTree(file_name="/phylobook/test_data/with_timepoints_misordered.svg")
        self.assertEqual(phylotree.swap_by_counts(), "Red, Neon Blue, Green, Black, Orange")
        self.assertIs(phylotree.swap_by_counts(), None)

        phylotree.save(file_name="/phylobook/test_data/with_timepoints_misordered_changed.svg")
        self.assertEqual(utils.file_hash(file_name="/phylobook/test_data/with_timepoints_misordered_changed.svg"), "e777e820d09d90611ad2528de13c4a52")
        
        os.remove("/phylobook/test_data/with_timepoints_misordered_changed.svg")

    def test_phylotree_swap_by_counts_correct_for_without_timepoints_misordered(self):
        """ PhyloTree swap_by_counts correct for without timepoints misordered """

        self.assertEqual(utils.file_hash(file_name="/phylobook/test_data/without_timepoints_misordered.svg"), "6e1d4b3d6fec7c5236c8746e3bfb7546")

        phylotree=utils.PhyloTree(file_name="/phylobook/test_data/without_timepoints_misordered.svg")
        self.assertEqual(phylotree.swap_by_counts(), "Red, Neon Blue")
        self.assertIs(phylotree.swap_by_counts(), None)

        phylotree.save(file_name="/phylobook/test_data/without_timepoints_misordered_changed.svg")
        self.assertEqual(utils.file_hash(file_name="/phylobook/test_data/without_timepoints_misordered_changed.svg"), "1f0c381cf022b62b57934068d853b483")
        
        os.remove("/phylobook/test_data/without_timepoints_misordered_changed.svg")

    def test_phylotree_should_count_unassigned_sequences(self):
        """ PhyloTree should count unassigned sequences """

        phylotree=utils.PhyloTree(file_name="/phylobook/test_data/with_timepoints_unassigned_sequences.svg")
        self.assertEqual(phylotree.unassigned_sequences, 55)

    def test_phylotree_should_show_no_unassigned_sequences_if_there_are_none(self):
        """ PhyloTree should show no unassigned sequences if there are none """

        self.assertEqual(self.phylotree.unassigned_sequences, 0)
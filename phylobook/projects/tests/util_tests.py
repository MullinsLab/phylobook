import logging
log = logging.getLogger('test')

from django.test import TestCase

from phylobook.projects.utils import tree_sequence_names, tree_lineage_counts, parse_sequence_name, get_lineage_dict


class TreeTests(TestCase):
    """ Tests that trees can be parsed """

    # Tests for tree_sequences

    def test_tree_sequences_should_return_none_given_none(self):
        """ tree_det_sequence_names should return None when given None """

        self.assertIs(tree_sequence_names(None), None)

    def test_tree_sequences_should_raise_exception_given_nonexistent_file(self):
        """ tree_det_sequence_names should raise an exception when given a nonexistent file """

        with self.assertRaises(FileNotFoundError):
            tree_lineage_counts("bad_name")

    def test_tree_sequences_should_return_list_of_dicts(self):
        """ tree_det_sequence_names should return a list """

        svg_file_name = "/phylobook/temp/test_with_timepoints.svg"
        sequences = tree_sequence_names(svg_file_name)

        self.assertIsInstance(sequences, list)
        self.assertIsInstance(sequences[0], dict)

    def test_tree_sequences_should_not_return_empty(self):
        """ tree_get_sequences should not return an empty list """
    
        svg_file_name = "/phylobook/temp/test_with_timepoints.svg"
        self.assertGreater(len(tree_sequence_names(svg_file_name)), 0)
    
    def test_tree_sequences_should_contain_particular_sequenc(self):
        """ tree_get_sequences should contain a particular sequence """
    
        svg_file_name = "/phylobook/temp/test_with_timepoints.svg"
        sequences = tree_sequence_names(svg_file_name)
        my_sequence = [sequence for sequence in sequences if sequence["name"] == "V703_0132_200_GP_NT_70_1"][0]

        self.assertTrue(my_sequence)
        self.assertEqual(my_sequence["color"], "green")

    # Tests for parse_sequences

    def test_parse_sequences_should_return_dict(self):
        """ parse_sequences should return a dict """

        sequence = parse_sequence_name("V703_0132_200_GP_NT_70_1")
        self.assertIsInstance(sequence, dict)

    def test_parse_sequences_should_not_return_none_when_given_none(self):
        """ parse_sequences should not return None when given None """

        sequence = parse_sequence_name(None)
        self.assertIs(sequence, None)

    def test_parse_sequences_should_return_correct_dict(self):
        """ parse_sequences should return a dict with the correct values """

        sequence = parse_sequence_name("V703_0132_200_GP_NT_70_1")
        self.assertEqual(sequence, {"timepoint": 200, "multiplicity": 1})

    def test_parse_sequences_should_return_none_with_no_multpilicity(self):
        """ parse_sequences should return None with a noncompliant name """

        sequence = parse_sequence_name("V703_0132_200_GP_NT_70_1_test")
        self.assertIs(sequence, None)

    def test_parse_sequences_should_return_value_with_no_timepoint(self):
        """ parse_sequences should return a dict with a no timepoint """

        sequence = parse_sequence_name("V703_0132_test_GP_NT_70_1")

        self.assertEquals(sequence["multiplicity"], 1)
        self.assertIs(sequence["timepoint"], None)

    # Tests for tree_lineage_counts
    # With test_with_timepoints.svg

    def test_tree_lineage_counts_should_return_dict(self):
        """ tree_lineage_counts should return a dict """

        svg_file_name = "/phylobook/temp/test_with_timepoints.svg"
        lineage_counts = tree_lineage_counts(svg_file_name)

        self.assertIsInstance(lineage_counts, dict)

    def test_tree_lineage_counts_should_not_return_empty(self):
        """ tree_lineage_counts should not return an empty list """

        svg_file_name = "/phylobook/temp/test_with_timepoints.svg"
        self.assertGreater(len(tree_lineage_counts(svg_file_name)), 0)

    def test_tree_lineage_counts_should_return_none_given_none(self):
        """ tree_lineage_counts should return None when given None """

        self.assertIs(tree_lineage_counts(None), None)

    def test_tree_lineage_counts_should_raise_error_given_bad_file_name(self):
        """ tree_lineage_counts should raise an error when given a bad file name """

        with self.assertRaises(FileNotFoundError):
            tree_lineage_counts("bad_name")

    def test_tree_lineage_counts_should_return_counts_for_colors(self):
        """ tree_lineage_counts should return counts for colors """

        svg_file_name = "/phylobook/temp/test_with_timepoints.svg"
        lineage_counts = tree_lineage_counts(svg_file_name)

        self.assertGreater(lineage_counts["red"]["timepoints"][200], 0)
    
    def test_tree_lineage_counts_should_be_less_than_total_count(self):
        """ tree_lineage_counts should be less than the total count """

        svg_file_name = "/phylobook/temp/test_with_timepoints.svg"
        lineage_counts = tree_lineage_counts(svg_file_name)

        self.assertLess(lineage_counts["red"]["timepoints"][200], 184)

    def test_tree_lineage_counts_should_be_178_for_red(self):
        """ tree_lineage_counts should be 178 for red """

        svg_file_name = "/phylobook/temp/test_with_timepoints.svg"
        lineage_counts = tree_lineage_counts(svg_file_name)

        self.assertEqual(lineage_counts["red"]["timepoints"][200], 178)

    # With test_with_timepoints.svg

    def test_tree_lineage_counts_should_return_counts_for_no_timepoints(self):
        """ tree_lineage_counts should return counts for colors """

        svg_file_name = "/phylobook/temp/test_without_timepoints.svg"
        lineage_counts = tree_lineage_counts(svg_file_name)

        self.assertGreater(lineage_counts["red"]["count"], 0)

    def test_tree_lineage_counts_should_be_37_for_red(self):
        """ tree_lineage_counts should be 37 for red """

        svg_file_name = "/phylobook/temp/test_without_timepoints.svg"
        lineage_counts = tree_lineage_counts(svg_file_name)

        self.assertEqual(lineage_counts["red"]["count"], 37)

    # Tests for lineage_dict

    def test_lineage_dict_should_return_dictionary(self):
        """ lineage_dict should return a dictionary """

        self.assertIsInstance(get_lineage_dict(), dict)

    def test_lineage_dict_should_return_red_names_correctly(self):
        """ lineage_dict should return a dictionary with correct red names """

        lineage_dict: dict = get_lineage_dict()
        self.assertEqual(lineage_dict["Red"], ['SxL', 'MxL1', 'MxL2', 'MxL3', 'MxL4', 'MxL5'])
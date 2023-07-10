from django.test import TestCase
from django.conf import settings

from phylobook.projects.models import Project, ProjectCategory, Tree, Lineage
from phylobook.projects.utils import tree_sequences, tree_lineage_counts, parse_sequence_name

# Create your tests here.
class ProjectTests(TestCase):
    """ Tests that projects can be set up correctly """

    def test_create_project(self):
        """ Create new project and make sure it"s name and tree_node are right """
       
        my_project = Project(name="My Project")
        my_project.save()

        self.assertEqual(str(my_project), "My Project")
        self.assertEqual(my_project.tree_node(), [{"My Project": {"depth": 1, "is_project": True}}])

    def test_add_project_to_category(self):
        """ Create a category and add our project to it """
        
        my_category = ProjectCategory.add_root(name="My Category")
        my_category.save()

        # Create a project with no category then add to category
        my_project_1 = Project(name="My Project 1") 
        my_project_1.save()
        my_project_1.category = my_category

        # Create a project with a category
        my_project_2 = Project(name="My Project 2", category = my_category)
        my_project_2.save()

        self.assertEqual(my_category.name, my_project_1.category.name)
        self.assertEqual(my_category.name, my_project_2.category.name)
        # self.assertEqual(my_category.tree_node(), [{"My Category", {"depth": 1, "is_project": False}}, {"My Project 1", {"depth": 2, "is_project": True}}, {"My Project 2", {"depth": 2, "is_project": True}}])


    def test_migration_should_create_lineages(self):
        """ Make sure that the migrate creates the correct lineages """

        self.assertGreater(Lineage.objects.all().count(), 0)
        self.assertEqual(Lineage.objects.all().filter(color="Red").count(), 2)


    def test_should_be_able_to_add_lineage_to_tree(self):
        """ Create a tree and add a lineage to it """

        project = Project(name="My Project 1") 
        project.save()

        tree = Tree(name="My Tree", project=project)
        tree.save()

        lineage = Lineage.objects.get(color="Red", lineage_name="SxL")

        tree.lineages.add(lineage)

        self.assertEqual(tree.lineages.all().first().lineage_name, "SxL")

class TreeTests(TestCase):
    """ Tests that trees can be parsed """

    # Tests for tree_sequences
    def test_tree_sequences_should_return_none_given_none(self):
        """ tree_det_sequence_names should return None when given None """

        self.assertIs(tree_sequences(None), None)

    def test_tree_sequences_should_raise_exception_given_nonexistent_file(self):
        """ tree_det_sequence_names should raise an exception when given a nonexistent file """

        with self.assertRaises(FileNotFoundError):
            tree_lineage_counts("bad_name")

    def test_tree_sequences_should_return_list_of_dicts(self):
        """ tree_det_sequence_names should return a list """

        tree_file_name = "/phylobook/temp/test.svg"
        sequences = tree_sequences(tree_file_name)

        self.assertIsInstance(sequences, list)
        self.assertIsInstance(sequences[0], dict)

    def test_tree_sequences_should_not_return_empty(self):
        """ tree_get_sequences should not return an empty list """
    
        tree_file_name = "/phylobook/temp/test.svg"
        self.assertGreater(len(tree_sequences(tree_file_name)), 0)
    
    def test_tree_sequences_should_contain_particular_sequenc(self):
        """ tree_get_sequences should contain a particular sequence """
    
        tree_file_name = "/phylobook/temp/test.svg"
        sequences = tree_sequences(tree_file_name)
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

    def test_parse_sequences_should_return_none_with_noncompliant_name(self):
        """ parse_sequences should return None with a noncompliant name """

        sequence = parse_sequence_name("V703_0132_200_GP_NT_70_1_test")
        self.assertIs(sequence, None)

        sequence = parse_sequence_name("V703_0132_test_GP_NT_70_1")
        self.assertIs(sequence, None)

    # Tests for tree_lineage_counts
    def test_tree_lineage_counts_should_return_dict(self):
        """ tree_lineage_counts should return a dict """

        tree_file_name = "/phylobook/temp/test.svg"
        lineage_counts = tree_lineage_counts(tree_file_name)

        self.assertIsInstance(lineage_counts, dict)

    def test_tree_lineage_counts_should_not_return_empty(self):
        """ tree_lineage_counts should not return an empty list """

        tree_file_name = "/phylobook/temp/test.svg"
        self.assertGreater(len(tree_lineage_counts(tree_file_name)), 0)

    def test_tree_lineage_counts_should_return_none_given_none(self):
        """ tree_lineage_counts should return None when given None """

        self.assertIs(tree_lineage_counts(None), None)

    def test_tree_lineage_counts_should_raise_error_given_bad_file_name(self):
        """ tree_lineage_counts should raise an error when given a bad file name """

        with self.assertRaises(FileNotFoundError):
            tree_lineage_counts("bad_name")

    def test_tree_lineage_counts_should_return_counts_for_colors(self):
        """ tree_lineage_counts should return counts for colors """

        tree_file_name = "/phylobook/temp/test.svg"
        lineage_counts = tree_lineage_counts(tree_file_name)

        self.assertGreater(lineage_counts["red"]["count"], 0)
    
    def test_tree_lineage_counts_should_be_less_than_total_count(self):
        """ tree_lineage_counts should be less than the total count """

        tree_file_name = "/phylobook/temp/test.svg"
        lineage_counts = tree_lineage_counts(tree_file_name)

        print(lineage_counts["neonblue"]["count"])

        self.assertLess(lineage_counts["red"]["count"], 184)
import logging
log = logging.getLogger('app')

from django.core.management.base import BaseCommand, CommandError

from phylobook.projects.models import Project
from phylobook.projects.utils.management import merge_projects


class Command(BaseCommand):
    """ Merge two projects into one """

    help = " Merges two projects."
    suppressed_base_arguments = ['--traceback', '--settings', '--pythonpath', '--skip-checks', '--no-color', '--version', '--force-color']

    def add_arguments(self, parser):
        """ Add arguments to the parser """
        parser.add_argument('project1_name', type=str, help="The name of the first project to merge")
        parser.add_argument('project2_name', type=str, help="The name of the second project to merge")
        parser.add_argument('new_project_name', type=str, help="The name of the new project")

    def handle(self, *args, **options):
        """ Do the work of merging projects """

        project1_name = options['project1_name']
        project2_name = options['project2_name']
        new_project_name = options['new_project_name']

        print(f"Merging {project1_name} and {project2_name} to {new_project_name}...")
        
        # get the projects
        try:
            project1 = Project.objects.get(name=project1_name)
        except Project.DoesNotExist:
            raise CommandError(f"Project {project1_name} does not exist.")
        
        try:
            project2 = Project.objects.get(name=project2_name)
        except Project.DoesNotExist:
            raise CommandError(f"Project {project2_name} does not exist.")

        try:
            merge_projects(project1=project1, project2=project2, new_project_name=new_project_name)
        except Exception as e:
            raise CommandError(f"Could not merge {project1_name} and {project2_name} to {new_project_name}: {e}")

        self.stdout.write(self.style.SUCCESS(f"Merged {project1_name} and {project2_name} to {new_project_name}"))
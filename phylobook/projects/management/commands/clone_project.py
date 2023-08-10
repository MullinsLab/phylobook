import logging
log = logging.getLogger('app')

from django.core.management.base import BaseCommand, CommandError

from phylobook.projects.models import Project


class Command(BaseCommand):
    """ Clone a project """

    help = " Clones a project."
    suppressed_base_arguments = ['--traceback', '--settings', '--pythonpath', '--skip-checks', '--no-color', '--version', '--force-color']

    def add_arguments(self, parser):
        """ Add arguments to the parser """
        parser.add_argument('project_name', type=str, help="The name of the project to clone")
        parser.add_argument('new_project_name', type=str, help="The name of the new project")

    def handle(self, *args, **options):
        """ Do the work of inspecting a file """

        project_name = options['project_name']
        new_project_name = options['new_project_name']

        # get the project
        try:
            project = Project.objects.get(name=project_name)
        except Project.DoesNotExist:
            raise CommandError(f"Project {project_name} does not exist.")

        try:
            project.clone(name=new_project_name)
        except Exception as e:
            raise CommandError(f"Could not clone project {project_name} to {new_project_name}: {e}")

        print(f"Cloning {project_name} to {new_project_name}...")

        self.stdout.write(self.style.SUCCESS(f"Project {project_name} has been cloned to {new_project_name}"))
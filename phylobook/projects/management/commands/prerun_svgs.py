import logging
log = logging.getLogger('app')

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from phylobook.projects.models import Project, Tree
from phylobook.projects.utils.tree import ensure_project_highlighter_svgs


class Command(BaseCommand):
    """ Pregenerate all highlighter SVGs for all projects """

    help = " Pregenerate all highlighter SVGs for all projects "
    suppressed_base_arguments = ['--traceback', '--settings', '--pythonpath', '--skip-checks', '--no-color', '--version', '--force-color']

    def add_arguments(self, parser):
        parser.add_argument('width',  nargs='?', type=int, help='Width of the marks in the plot', default=settings.HIGHLIGHTER_MARK_WIDTH)

    def handle(self, *args, **options):
        """ Do the work of building all highlighter SVGs """

        for project in Project.objects.all():
            print(f"Processing {project}")
            errors: list = ensure_project_highlighter_svgs(project, width=options["width"])
            
            for error_list in errors:
                for error in error_list:
                    if error:
                        self.stdout.write(self.style.ERROR(error))

        self.stdout.write(self.style.SUCCESS(f'All highlighter SVGs generated'))
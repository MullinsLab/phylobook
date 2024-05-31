import logging
log = logging.getLogger('app')

from django.core.management.base import BaseCommand, CommandError

from phylobook.projects.utils.processes import check_processes, start_next_process

class Command(BaseCommand):
    """ Process imported .fasta files"""

    help = "Processes imported .fasta files."
    suppressed_base_arguments = ['--traceback', '--settings', '--pythonpath', '--skip-checks', '--no-color', '--version', '--force-color']

    def handle(self, *args, **options):
        """ Do the work of processing files """

        check_processes()
        ran: bool = start_next_process()

        if ran:
            self.stdout.write(self.style.SUCCESS(f"Processed a .fasta file."))
        else:
            self.stdout.write(self.style.NOTICE("No .fasta files to process."))
import logging
log = logging.getLogger('app')

import csv

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from phylobook.projects.models import Lineage


class Command(BaseCommand):
    """ Update lineages for all projects """

    help = " Replaces all lineage names in the database from a CSV file. "
    suppressed_base_arguments = ['--traceback', '--settings', '--pythonpath', '--skip-checks', '--no-color', '--version', '--force-color']

    def handle(self, *args, **options):
        """ Do the work of inspecting a file """

        # check the file for gross errors
        with open(settings.LINEAGE_FILE) as lineage_file:
            reader: csv.DictReader = csv.DictReader(lineage_file)
            for row in reader:
                if (row["color"] not in [color["name"] for color in settings.ANNOTATION_COLORS] and row["color"] != "Ordering") or not row["lineage_name"]:
                    raise CommandError(f"{settings.LINEAGE_FILE} is malformed.  Every row must have a color from ANNOTATION_COLORS, and a lineage_name.\nBad row: {row}")

        # delete all lineages
        Lineage.objects.all().delete()

        # create new lineages
        with open(settings.LINEAGE_FILE) as lineage_file:
            reader: csv.DictReader = csv.DictReader(lineage_file)
            for row in reader:
                Lineage.objects.create(**row)
                print(row)

        self.stdout.write(self.style.SUCCESS(f"Lineages have been updated from {settings.LINEAGE_FILE}"))
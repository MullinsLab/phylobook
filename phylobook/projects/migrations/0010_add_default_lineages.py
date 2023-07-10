import csv
from django.db import migrations
from django.conf import settings


def add_default_lineages(apps, schema_editor):
    """ Create lineages """

    if not hasattr(settings, 'LINEAGE_FILE'):
        return

    Lineage = apps.get_model('projects', 'Lineage')

    with open(settings.LINEAGE_FILE) as lineage_file:
        reader = csv.DictReader(lineage_file)
        for row in reader:
            Lineage.objects.create(**row)


def remove_default_lineages(apps, schema_editor):
    """ Remove lineages """

    Lineage = apps.get_model('projects', 'Lineage')

    Lineage.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0009_auto_20230710_0320'),
    ]

    operations = [
        migrations.RunPython(add_default_lineages, remove_default_lineages)
    ]

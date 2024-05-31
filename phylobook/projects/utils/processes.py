""" Holds functions that deal with file processing """

import logging
log = logging.getLogger('app')

from django.conf import settings as django_settings


from phylobook.projects.models import Process


def check_processes() -> bool:
    """ Checks all processes that are marked as Started """

    for process in Process.objects.filter(status="Running"):
        process.check_health()


def start_next_process():
    """ Starts the next process in the queue """

    if Process.objects.filter(status="Running").count() < django_settings.MAX_FASTA_PROCESSORS:
        if process := Process.objects.filter(status="Pending").first():        
            process.run()

            return True
    
    return False


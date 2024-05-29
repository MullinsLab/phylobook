""" Holds functions that deal with file processing """

from phylobook.projects.models import Process

def check_processes() -> bool:
    """ Checks all processes that are marked as Started """

    for process in Process.objects.filter(status="Started"):
        process.check_health()
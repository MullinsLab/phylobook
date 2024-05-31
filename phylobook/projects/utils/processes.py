""" Holds functions that deal with file processing """

from phylobook.projects.models import Process


def check_processes() -> bool:
    """ Checks all processes that are marked as Started """

    for process in Process.objects.filter(status="Running"):
        process.check_health()


def start_next_process():
    """ Starts the next process in the queue """

    if process := Process.objects.filter(status="Pending").first():
        print(f"Starting - {process}")
        
        process.run()


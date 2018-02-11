from django.core.management.base import BaseCommand, CommandError

from registration.models import export_registrations

class Command(BaseCommand):
    help = 'Export a csv file of the registered participents.'

    def add_arguments(self, parser):
        parser.add_argument('file', nargs=1, type=str)

    def handle(self, *args, **options):
        f = open(options['file'][0], 'w', newline='')
        export_registrations(f)
        
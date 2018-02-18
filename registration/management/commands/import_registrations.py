from django.core.management.base import BaseCommand, CommandError

from registration.models import import_registrations

class Command(BaseCommand):
    help = 'Import a csv file from Google Forms.'

    def add_arguments(self, parser):
        parser.add_argument('file', nargs=1, type=str)

    def handle(self, *args, **options):
        f = open(options['file'][0], newline='')
        stats = import_registrations(f)
        self.stdout.write(self.style.SUCCESS('Added {added}, skipped {skipped}.'.format(**stats)))
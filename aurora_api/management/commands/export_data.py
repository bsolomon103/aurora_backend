# myapp/management/commands/export_data.py

import csv
from django.core.management.base import BaseCommand
from aurora_api.models import Chat  # Import your model

class Command(BaseCommand):
    help = 'Export data to CSV file'

    def handle(self, *args, **options):
        # Specify the file path for the CSV file
        csv_file_path = 'output_data.csv'

        # Fetch data from the model
        data = Chat.objects.values()

        # Write data to CSV file
        with open(csv_file_path, 'w', newline='') as csv_file:
            csv_writer = csv.DictWriter(csv_file, fieldnames=data[0].keys())
            csv_writer.writeheader()
            csv_writer.writerows(data)

        self.stdout.write(self.style.SUCCESS(f'Data exported to {csv_file_path}'))

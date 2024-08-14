import random

from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from faker import Faker

from core.models import Person, SpamReport, UserContact


class Command(BaseCommand):
    """
    Run the command using 
    python manage.py populate_db --num_users 10 --num_contacts 50 --num_spam_reports 20
    """
    help = 'Populate the database with sample data'

    def add_arguments(self, parser):
        """
        Add optional arguments for the command.
        """
        parser.add_argument(
            '--num_users', type=int, default=100, help='Number of users to create'
            )
        parser.add_argument(
            '--num_contacts', type=int, default=200, help='Number of contacts to create'
            )
        parser.add_argument(
            '--num_spam_reports', type=int, default=200, help='Number of spam reports to create'
        )

    def handle(self, *args, **kwargs):
        num_users = kwargs['num_users']
        num_contacts = kwargs['num_contacts']
        num_spam_reports = kwargs['num_spam_reports']

        fake = Faker()

        # Clear existing data
        Person.objects.all().delete()

        # Create users
        for _ in range(num_users):
            Person.objects.create(
                name=fake.name(),
                phone_number=fake.unique.phone_number()[:15],
                email=fake.email(),
                password=make_password(fake.password()),
                type='user'
            )

        # Create contacts
        person_ids = Person.objects.values_list('pk', flat=True)
        for _ in range(num_contacts):
            user_contact_list = random.sample(set(person_ids), 2)
            UserContact.objects.create(
                name=fake.name(),
                user_id=user_contact_list[0],
                contact_id=user_contact_list[1]
            )

        # Create spam numbers
        for _ in range(num_spam_reports):
            user_contact_list = random.sample(set(person_ids), 2)
            SpamReport.objects.create(
                reported_by_id=user_contact_list[0],
                spam_person_id=user_contact_list[1]
            )

        self.stdout.write('Database populated with sample data')

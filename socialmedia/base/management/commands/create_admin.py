from django.core.management.base import BaseCommand
from base.models import User
from django.core.management import CommandError

class Command(BaseCommand):
    help = 'Create a superuser/admin with specified name, email, and password'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email of the superuser')
        parser.add_argument('name', type=str, help='Name of the superuser')
        parser.add_argument('password', type=str, help='Password for the superuser')

    def handle(self, *args, **options):
        email = options['email']
        name = options['name']
        password = options['password']

        if User.objects.filter(email=email).exists():
            raise CommandError(f'User with email "{email}" already exists.')

        user = User.objects.create_superuser(email=email, name=name, password=password)
        user.first_name = name
        user.save()
        self.stdout.write(self.style.SUCCESS(f'Superuser "{email}" created successfully.'))

# email = thunderpixel000@gmail.com
# name = Ravi
# password = Pixel123@
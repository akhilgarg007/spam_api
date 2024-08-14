from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from core.managers import PersonManager


class Person(AbstractBaseUser, PermissionsMixin):
    """
    Model representing a person which can be a user, contact, or spam person.
    """
    USER_TYPE_CHOICES = (
        ('user', 'User'),
        ('contact', 'Contact'),
        ('spam', 'Spam'),
    )

    name = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(null=True, blank=True)
    password = models.CharField(max_length=128, null=True, blank=True)
    type = models.CharField(max_length=7, choices=USER_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = PersonManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['name']

    @property
    def is_staff(self):
        return self.is_admin

    def __str__(self):
        return f'{self.name}->{self.phone_number}->{self.type}'


class UserContact(models.Model):
    """
    Model representing the many-to-many relationship between users and contacts.
    """
    name = models.CharField(max_length=255)
    user = models.ForeignKey(Person, related_name='user_contacts', on_delete=models.CASCADE)
    contact = models.ForeignKey(Person, related_name='contact_users', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name}->{self.user.phone_number}->{self.contact.phone_number}'


class SpamReport(models.Model):
    """
    Model representing a spam report.
    """
    reported_by = models.ForeignKey(Person, related_name='spam_reports', on_delete=models.CASCADE)
    spam_person = models.ForeignKey(
        Person, related_name='spam_reports_as_spam', null=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.reported_by.phone_number}->{self.spam_person.phone_number}'

from django.contrib.auth.models import BaseUserManager


class PersonManager(BaseUserManager):
    """
    Custom manager for the Person model to handle user creation.
    """
    def create_user(self, phone_number, name, password=None, email=None, user_type='user'):
        """
        Create and return a user with the given phone number, name, and password.
        """
        if not phone_number:
            raise ValueError("Users must have a phone number")
        user = self.model(
            phone_number=phone_number,
            name=name,
            email=self.normalize_email(email),
            type=user_type
        )
        user.set_password(password)
        user.save()
        return user

    def create_contact(self, phone_number, name):
        """
        Create and return a contact with the given phone number and name.
        """
        contact = self.model(
            phone_number=phone_number,
            name=name,
            type='contact',
        )
        contact.save()
        return contact

    def create_spam_person(self, phone_number):
        """
        Create and return a spam person with the given phone number.
        """
        spam_person = self.model(
            phone_number=phone_number,
            type='spam',
        )
        spam_person.save()
        return spam_person

    def create_superuser(self, phone_number, name, password, email=None):
        """
        Create and return a superuser with the given phone number, name, and password.
        """
        user = self.create_user(phone_number, name, password, email)
        user.is_admin = True
        user.is_superuser = True
        user.save()
        return user
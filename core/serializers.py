from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from core.models import Person, SpamReport, UserContact


class PersonSerializer(serializers.ModelSerializer):
    """
    Serializer for the Person model.
    """
    phone_number = serializers.CharField(max_length=15)

    class Meta:
        model = Person
        fields = ['id', 'name', 'phone_number', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True, 'required': True},
            'name': {'required': True}
        }

    def validate_password(self, password):
        """
        Validate function to validate password
        """
        validate_password(password)
        return password

    def create(self, validated_data):
        """
        Create and return a person. If a contact or spam person with the same phone number exists,
        update it to be a user.
        """
        phone_number = validated_data['phone_number']
        existing_person = Person.objects.filter(phone_number=phone_number).first()

        if existing_person:
            if existing_person.type in ['contact', 'spam']:
                existing_person.name = validated_data['name']
                existing_person.email = validated_data.get('email', existing_person.email)
                existing_person.set_password(validated_data['password'])
                existing_person.type = 'user'
                existing_person.save()
                return existing_person
            else:
                raise serializers.ValidationError("A user with this phone number already exists.")
        else:
            return Person.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """
    Serializer for the Login View
    """
    phone_number = serializers.CharField(max_length=15)
    password = serializers.CharField()


class ProfileQueryParamSerializer(serializers.Serializer):
    """
    Serializer for the profile query params
    """
    phone_number = serializers.CharField(max_length=15)


class SpamReportSerializer(serializers.ModelSerializer):
    """
    Serializer for the SpamReport model.
    """
    phone_number = serializers.CharField(write_only=True)

    class Meta:
        model = SpamReport
        fields = ['id', 'phone_number']
    
    def create(self, validated_data):
        """
        Create and return a SpamReport. If the spam person doesn't exist, create a new one.
        """
        if validated_data['phone_number'] == self.context['request'].user.phone_number:
            raise serializers.ValidationError('Can\'t report self as spam.')
        spam_person, _ = Person.objects.get_or_create(
            phone_number=validated_data['phone_number'],
            defaults={'type': 'spam'}
        )
        spam_report, created = SpamReport.objects.get_or_create(
            reported_by=validated_data['reported_by'],
            spam_person=spam_person
        )
        if created:
            return spam_report
        else:
            raise serializers.ValidationError('Spam report already exists.')


class UserContactSerializer(serializers.ModelSerializer):
    """
    Serializer for the UserContact model, accepting phone number and name of the contact.
    """
    phone_number = serializers.CharField(max_length=15, write_only=True)

    class Meta:
        model = UserContact
        fields = ['phone_number', 'name', 'id']

    def validate(self, attrs):
        """
        Validate that the contact is not already in the user's contact list.
        """
        phone_number = attrs['phone_number']
        user = self.context['request'].user
        if UserContact.objects.filter(user=user, contact__phone_number=phone_number).exists():
            raise serializers.ValidationError("Contact already exists in your contact list.")
        return attrs

    def create(self, validated_data):
        """
        Create and return a UserContact. If the contact doesn't exist, create a new Person object.
        """
        phone_number = validated_data['phone_number']
        name = validated_data['name']
        user = self.context['request'].user

        contact_person, _ = Person.objects.get_or_create(
            phone_number=phone_number,
            defaults={'name': name, 'type': 'contact'}
        )
        return UserContact.objects.create(user=user, contact=contact_person, name=name)
    

class UserContactOutputSerializer(serializers.ModelSerializer):
    """
    Serializer for the UserContact model, outputting the contact details
    """
    phone_number = serializers.SerializerMethodField()

    class Meta:
        model = UserContact
        fields = ['user', 'phone_number', 'name', 'id']

    def get_phone_number(self, user_contact):
        """
        Return the phone number of the contact
        """
        return user_contact.contact.phone_number
    

class SearchQueryParamSerializer(serializers.Serializer):
    """
    Serializer for search query params
    """
    NAME = 'name'
    PHONE_NUMBER = 'phone_number'
    SEARCH_BY_CHOICES = [
        (NAME, 'Name'),
        (PHONE_NUMBER, 'Phone Number'),
    ]
    search_by = serializers.ChoiceField(choices=SEARCH_BY_CHOICES)
    phone_number = serializers.CharField(max_length=15, required=False)
    name = serializers.CharField(max_length=255, min_length=3, required=False)

    def validate(self, attrs):
        """
        Validate that name is given when search by is name and same for phone number
        """
        if attrs['search_by'] == self.NAME and not attrs.get('name'):
            raise serializers.ValidationError('Name is required when search by is name')
        if attrs['search_by'] == self.PHONE_NUMBER and not attrs.get('phone_number'):
            raise serializers.ValidationError('Phone number is required when search by is phone_number')
        return attrs


class SearchResultSerializer(serializers.ModelSerializer):
    """
    Serializer for the Person search result.
    """
    spam_reports = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = Person
        fields = ['name', 'phone_number', 'spam_reports']

    def get_name(self, person):
        if hasattr(person, 'display_name'):
            return person.display_name
        return person.name

    def get_spam_reports(self, person):
        return SpamReport.objects.filter(
            spam_person__phone_number=person.phone_number
        ).count()

from django.contrib.auth import authenticate
from django.db.models import Case, F, CharField, OuterRef, Q, Subquery, Value, When
from rest_framework import generics, permissions
from rest_framework.authtoken.models import Token
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from core.models import Person, SpamReport, UserContact
from core.serializers import (
    LoginSerializer,
    PersonSerializer,
    ProfileQueryParamSerializer,
    SearchResultSerializer,
    SearchQueryParamSerializer,
    SpamReportSerializer,
    UserContactSerializer,
    UserContactOutputSerializer
)


class RegisterView(generics.CreateAPIView):
    """
    API view to register a new user.
    """
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    permission_classes = []

    def perform_create(self, serializer):
        """
        Set the person type to 'user' upon registration.
        """
        serializer.save(user_type='user')


class LoginView(generics.GenericAPIView):
    """
    API view to log in a user and return a token.
    """
    serializer_class = LoginSerializer
    permission_classes = []

    def post(self, request, *args, **kwargs):
        """
        Authenticate the user and return a token if credentials are valid.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            phone_number=serializer.validated_data['phone_number'],
            password=serializer.validated_data['password']
        )
        if user is not None:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key})
        return Response({'error': 'Invalid Credentials'}, status=400)


class ProfileView(generics.RetrieveAPIView):
    """
    API view to retrieve the profile of any user.
    """
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """
        Return the user whose phone number is provided
        """
        query_params = ProfileQueryParamSerializer(data=self.request.query_params)
        query_params.is_valid(raise_exception=True)
        person = Person.objects.filter(phone_number=query_params.validated_data['phone_number']).first()
        if person:
            # Not adding registered user check here as only registered users will have email populated.
            show_email = UserContact.objects.filter(user=person, contact=self.request.user).exists() or person==self.request.user
            if not show_email:
                person.email = None
        return person



class ContactView(generics.ListCreateAPIView):
    """
    API view to list and create user contacts.
    """
    queryset = UserContact.objects.all().select_related('contact')
    serializer_class = UserContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserContactOutputSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """
        Create a contact for the logged-in user.
        """
        serializer.save()

    def get_queryset(self):
        """
        Return the contacts of the logged-in user.
        """
        return self.queryset.filter(user=self.request.user)


class SpamReportView(generics.CreateAPIView):
    """
    API view to create a spam report.
    """
    queryset = SpamReport.objects.all()
    serializer_class = SpamReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """
        Create a spam report and link it to the logged-in user. If the spam person doesn't exist,
        create a new one.
        """
        serializer.validated_data['reported_by'] = self.request.user
        serializer.save()


class SearchView(generics.ListAPIView):
    """
    API view to search for people by name or phone number.
    """
    serializer_class = SearchResultSerializer
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        """
        Handle search requests and return search results queryset.
        """
        query_params = SearchQueryParamSerializer(data=self.request.query_params)
        query_params.is_valid(raise_exception=True)
        search_by = query_params.validated_data['search_by']

        if search_by == SearchQueryParamSerializer.NAME:
            results = self.get_people_by_name(
                query_params.validated_data['name']
            )
        elif search_by == SearchQueryParamSerializer.PHONE_NUMBER:
            results = self.get_people_by_phone_number(
                query_params.validated_data['phone_number']
            )
        return results

    def get_people_by_phone_number(self, search_query):
        """
        Handle search requests by phone number and return search results queryset.
        """
        person = Person.objects.filter(phone_number=search_query, type='user')
        if person:
            return person
        raw_query = """
            SELECT 
                p.id,
                p.phone_number AS phone_number,
                uc.name AS name
            FROM 
                core_person p
            INNER JOIN 
                core_usercontact uc ON p.id = uc.contact_id
            WHERE 
                uc.id IS NOT NULL AND p.phone_number = %s
        """
        return Person.objects.raw(raw_query, [search_query])


    def get_people_by_name(self, search_query):
        """
        Handle search requests by name and return search results queryset.
        """
        # This will have the side effect of adding Persons name whose contact name includes the
        # search query but their name doesn't includes the search query which is intentional as
        # they are ordered last and it will expose the real name of the same phone number to
        # the user
        base_qs = Person.objects.annotate(
            display_name=Case(
                When(contact_users__name__icontains=search_query, then=F('contact_users__name')),
                default=F('name'),
                output_field=CharField()
            ),
            order_field=Case(
                When(
                    Q(name__istartswith=search_query) |
                    Q(contact_users__name__istartswith=search_query),
                    then=Value('1')
                ),
                When(
                    Q(name__icontains=search_query) |
                    Q(contact_users__name__icontains=search_query),
                    then=Value('2')
                ),
                default=Value('3'),
                output_field=CharField()
            )
        ).filter(
            Q(name__icontains=search_query) | Q(contact_users__name__icontains=search_query)
        )
        final_qs = base_qs.order_by('order_field', 'display_name')
        return final_qs.distinct()

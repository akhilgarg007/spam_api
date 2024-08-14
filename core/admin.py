from django.contrib import admin

from core.models import Person, UserContact, SpamReport


admin.site.register(Person)
admin.site.register(UserContact)
admin.site.register(SpamReport)

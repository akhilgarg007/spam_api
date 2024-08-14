from django.urls import path
from core.views import RegisterView, LoginView, ProfileView, ContactView, SpamReportView, SearchView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('contacts/', ContactView.as_view(), name='contacts'),
    path('spam/', SpamReportView.as_view(), name='spam'),
    path('search/', SearchView.as_view(), name='search'),
]

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    
    # Validation APIs for HTMX
    path('validate-email/', views.validate_email, name='validate_email'),
    path('validate-nickname/', views.validate_nickname, name='validate_nickname'),
]

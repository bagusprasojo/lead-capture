from django.contrib.auth import views as auth_views
from django.urls import path

from .forms import LoginForm
from .views import (
    CSVExportView,
    DashboardView,
    EmbedScriptView,
    HomeView,
    LeadDeleteView,
    LeadUpdateView,
    ProfileView,
    PublicLeadCaptureView,
    SignupView,
)

app_name = 'leads'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('signup/', SignupView.as_view(), name='signup'),
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='registration/login.html',
            authentication_form=LoginForm,
        ),
        name='login',
    ),
    path(
        'logout/',
        auth_views.LogoutView.as_view(),
        name='logout',
    ),
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='registration/password_reset_form.html'
        ),
        name='password_reset',
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/password_reset_done.html'
        ),
        name='password_reset_done',
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm.html'
        ),
        name='password_reset_confirm',
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html'
        ),
        name='password_reset_complete',
    ),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('leads/<int:pk>/edit/', LeadUpdateView.as_view(), name='lead_edit'),
    path(
        'leads/<int:pk>/delete/',
        LeadDeleteView.as_view(),
        name='lead_delete',
    ),
    path('leads/export/', CSVExportView.as_view(), name='export_csv'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('public/form/<str:public_id>/', PublicLeadCaptureView.as_view(), name='public_form'),
    path('public/embed/<str:public_id>.js', EmbedScriptView.as_view(), name='embed_script'),
]

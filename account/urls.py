from django.urls import path
from django.contrib.auth import views as auth_views
from . import views


app_name = 'account'


urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('edit/', views.edit_account, name="edit_account"),
    path('add-address/', views.add_address, name='add_address'),
    path('edit-address/<int:address_id>/', views.edit_address, name='edit_address'),
    path('delete-address/', views.delete_address, name='delete_address'),
    path('api/my-addresses/', views.user_addresses_partial, name='user_addresses_partial'),
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='account/password_reset_form.html',success_url='/account/password-reset/done/',
        email_template_name='account/password_reset_email.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='account/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='account/password_reset_confirm.html',
        success_url='/account/password-reset/complete/'), name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='account/password_reset_complete.html'), name='password_reset_complete'),
]
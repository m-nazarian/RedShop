from django.urls import path
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
]
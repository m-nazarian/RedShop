from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin
from .forms import ShopUserCreationForm, ShopUserChangeForm


@admin.register(ShopUser)
class ShopUserAdmin(UserAdmin):
    ordering = ['phone']
    add_form = ShopUserCreationForm
    form = ShopUserChangeForm
    model = ShopUser
    list_display = ['phone', 'first_name', 'last_name', 'is_staff', 'is_active']
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name','address')}),
        ('Permissions', {'fields': ('is_active','is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {'fields': ('phone', 'password1', 'password2')}),
        ('Personal info', {'fields': ('first_name', 'last_name','address')}),
        ('Permissions', {'fields': ('is_active','is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['display_name' ,'user',  'date_of_birth', 'id_card']
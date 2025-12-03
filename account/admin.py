from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from .models import *
from .forms import ShopUserCreationForm, ShopUserChangeForm


@admin.register(ShopUser)
class ShopUserAdmin(BaseUserAdmin, ModelAdmin):
    add_form = ShopUserCreationForm
    form = ShopUserChangeForm
    change_password_form = AdminPasswordChangeForm

    ordering = ['phone']
    list_display = ['phone', 'first_name', 'last_name', 'email', 'is_staff', 'is_active']
    search_fields = ['phone', 'email', 'first_name', 'last_name']

    fieldsets = (
        (None, {'fields': ('phone', 'email', 'password')}),
        ('اطلاعات شخصی', {'fields': ('first_name', 'last_name', 'address')}),
        ('دسترسی‌ها', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('تاریخ‌ها', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {'fields': ('phone', 'email', 'password1', 'password2')}),
        ('اطلاعات شخصی', {'fields': ('first_name', 'last_name', 'address')}),
        ('دسترسی‌ها', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )


@admin.register(Account)
class AccountAdmin(ModelAdmin):
    list_display = ['display_name', 'user', 'date_of_birth', 'id_card']
    search_fields = ['user__phone', 'user__first_name', 'id_card']

from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Account, Address, ShopUser


def normalize_iranian_mobile(phone):
    """Return a canonical local mobile number used by authentication forms."""
    return (phone or "").strip()


def validate_iranian_mobile(phone):
    """Validate the phone format used as the project's username field."""
    phone = normalize_iranian_mobile(phone)

    if not phone:
        raise forms.ValidationError("شماره تلفن الزامی است.")

    if not phone.isdigit():
        raise forms.ValidationError("شماره تلفن باید فقط عدد باشد.")

    if not phone.startswith("09"):
        raise forms.ValidationError("شماره تلفن باید با 09 شروع شود.")

    if len(phone) != 11:
        raise forms.ValidationError("شماره تلفن باید 11 رقم باشد.")

    return phone


class ShopUserCreationForm(UserCreationForm):
    """Admin user creation form with the same phone validation as the storefront."""

    class Meta(UserCreationForm.Meta):
        model = ShopUser
        fields = (
            "phone",
            "email",
            "first_name",
            "last_name",
            "address",
            "is_active",
            "is_staff",
            "is_superuser",
        )

    def clean_phone(self):
        phone = validate_iranian_mobile(self.cleaned_data.get("phone"))

        if ShopUser.objects.filter(phone=phone).exists():
            raise forms.ValidationError("این شماره تلفن قبلا ثبت شده است.")

        return phone

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()

        if not email:
            return None

        if ShopUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("این ایمیل قبلا ثبت شده است.")

        return email


class ShopUserChangeForm(UserChangeForm):
    """Admin user edit form that keeps phone and email unique."""

    class Meta(UserChangeForm.Meta):
        model = ShopUser
        fields = (
            "phone",
            "email",
            "first_name",
            "last_name",
            "address",
            "is_active",
            "is_staff",
            "is_superuser",
        )

    def clean_phone(self):
        phone = validate_iranian_mobile(self.cleaned_data.get("phone"))

        qs = ShopUser.objects.filter(phone=phone)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError("این شماره تلفن توسط کاربر دیگری استفاده شده است.")

        return phone

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()

        if not email:
            return None

        qs = ShopUser.objects.filter(email__iexact=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError("این ایمیل توسط کاربر دیگری استفاده شده است.")

        return email


class UserRegistrationForm(forms.ModelForm):
    """Public registration form.

    The password is validated through Django's configured password validators,
    so weak, numeric-only, common, or user-similar passwords are rejected before
    the account is created.
    """

    password = forms.CharField(
        max_length=250,
        required=True,
        widget=forms.PasswordInput(),
        label="رمز عبور",
    )
    password2 = forms.CharField(
        max_length=250,
        required=True,
        widget=forms.PasswordInput(),
        label="تکرار رمز عبور",
    )

    class Meta:
        model = ShopUser
        fields = ["phone"]
        widgets = {
            "phone": forms.TextInput(),
        }

    def clean_phone(self):
        phone = validate_iranian_mobile(self.cleaned_data.get("phone"))

        if ShopUser.objects.filter(phone=phone).exists():
            raise forms.ValidationError("این شماره تلفن قبلا ثبت شده است.")

        return phone

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")
        phone = cleaned_data.get("phone")

        if password and password2 and password != password2:
            self.add_error("password2", "رمز عبورها مطابقت ندارند.")

        if password:
            candidate_user = ShopUser(phone=phone or "")
            try:
                validate_password(password, user=candidate_user)
            except ValidationError as exc:
                self.add_error("password", exc)

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

        return user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = "input__login__input"

        placeholders = {
            "phone": "شماره تلفن همراه",
            "password": "رمز عبور خود را وارد کنید",
            "password2": "رمز عبور خود را تکرار کنید",
        }

        for field_name, placeholder in placeholders.items():
            if field_name in self.fields:
                self.fields[field_name].widget.attrs["placeholder"] = placeholder


class UserEditForm(forms.ModelForm):
    """Profile form for non-sensitive user data.

    Email is intentionally editable here because password reset requires a
    reachable email address for users who registered with phone number only.
    """

    class Meta:
        model = ShopUser
        fields = ["first_name", "last_name", "email", "address"]
        labels = {
            "first_name": "نام",
            "last_name": "نام خانوادگی",
            "email": "ایمیل",
            "address": "آدرس",
        }

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()

        if not email:
            return None

        qs = ShopUser.objects.filter(email__iexact=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError("این ایمیل توسط کاربر دیگری استفاده شده است.")

        return email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs.update(
                {
                    "class": (
                        "w-full border border-gray-200 rounded-lg px-4 py-2.5 "
                        "text-sm focus:outline-none focus:border-blue-500 "
                        "focus:ring-4 focus:ring-blue-500/10 transition-all"
                    )
                }
            )


class AccountEditForm(forms.ModelForm):
    """Public account form.

    Bank account/card numbers and national IDs are deliberately not collected in
    the public profile UI. Keeping sensitive identifiers out of ordinary profile
    forms is safer than storing plaintext values that are not needed for the
    current storefront flow.
    """

    class Meta:
        model = Account
        fields = ["date_of_birth", "photo"]
        labels = {
            "date_of_birth": "تاریخ تولد",
            "photo": "تصویر پروفایل",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields:
            if field == "photo":
                self.fields[field].widget.attrs.update(
                    {
                        "class": (
                            "block w-full text-sm text-gray-500 file:mr-4 "
                            "file:py-2 file:px-4 file:rounded-full file:border-0 "
                            "file:text-sm file:font-semibold file:bg-blue-50 "
                            "file:text-blue-700 hover:file:bg-blue-100"
                        )
                    }
                )
            else:
                self.fields[field].widget.attrs.update(
                    {
                        "class": (
                            "w-full border border-gray-200 rounded-lg px-4 py-2.5 "
                            "text-sm focus:outline-none focus:border-blue-500 "
                            "focus:ring-4 focus:ring-blue-500/10 transition-all"
                        )
                    }
                )


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            "first_name",
            "last_name",
            "address_line",
            "city",
            "province",
            "postal_code",
            "phone",
        ]
        labels = {
            "first_name": "نام گیرنده",
            "last_name": "نام خانوادگی گیرنده",
            "address_line": "آدرس کامل",
            "city": "شهر",
            "province": "استان",
            "postal_code": "کد پستی",
            "phone": "شماره تماس",
        }

    def clean_phone(self):
        return validate_iranian_mobile(self.cleaned_data.get("phone"))

    def clean_postal_code(self):
        postal_code = (self.cleaned_data.get("postal_code") or "").strip()

        if not postal_code.isdigit():
            raise forms.ValidationError("کد پستی باید فقط عدد باشد.")

        if len(postal_code) != 10:
            raise forms.ValidationError("کد پستی باید ۱۰ رقم باشد.")

        return postal_code

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs.update(
                {
                    "class": (
                        "w-full border border-gray-200 rounded-lg px-4 py-2.5 "
                        "text-sm focus:outline-none focus:border-blue-500 "
                        "focus:ring-4 focus:ring-blue-500/10 transition-all"
                    )
                }
            )

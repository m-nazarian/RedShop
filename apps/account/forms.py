from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import ShopUser, Account, Address


# ---------------------------------------
# فرم‌های مخصوص پنل ادمین (Admin Panel)
# ---------------------------------------

class ShopUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = ShopUser
        fields = ('phone', 'first_name', 'last_name', 'address', 'is_active', 'is_staff', 'is_superuser')

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')

        # بررسی وجود کاربر
        if ShopUser.objects.filter(phone=phone).exists():
            raise forms.ValidationError('این شماره تلفن قبلا ثبت شده است.')

        # اعتبارسنجی فرمت
        if not phone.isdigit():
            raise forms.ValidationError('شماره تلفن باید فقط عدد باشد.')
        if not phone.startswith('09'):
            raise forms.ValidationError('شماره تلفن باید با 09 شروع شود.')
        if len(phone) != 11:
            raise forms.ValidationError('شماره تلفن باید 11 رقم باشد.')

        return phone


class ShopUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = ShopUser
        fields = ('phone', 'first_name', 'last_name', 'address', 'is_active', 'is_staff', 'is_superuser')

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')

        qs = ShopUser.objects.filter(phone=phone)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError('این شماره تلفن توسط کاربر دیگری استفاده شده است.')

        # اعتبارسنجی فرمت
        if not phone.isdigit():
            raise forms.ValidationError('شماره تلفن باید فقط عدد باشد.')
        if not phone.startswith('09'):
            raise forms.ValidationError('شماره تلفن باید با 09 شروع شود.')
        if len(phone) != 11:
            raise forms.ValidationError('شماره تلفن باید 11 رقم باشد.')

        return phone


# ---------------------------------------
# فرم‌های سمت کاربر (Front-end)
# ---------------------------------------

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        max_length=250,
        required=True,
        widget=forms.PasswordInput(),
        label='رمز عبور'
    )
    password2 = forms.CharField(
        max_length=250,
        required=True,
        widget=forms.PasswordInput(),
        label='تکرار رمز عبور'
    )

    class Meta:
        model = ShopUser
        fields = ['phone']
        widgets = {
            'phone': forms.TextInput(),
        }

    def clean_password2(self):
        cd = self.cleaned_data
        if cd.get('password') != cd.get('password2'):
            raise forms.ValidationError("رمز عبورها مطابقت ندارند!")
        return cd['password2']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if ShopUser.objects.filter(phone=phone).exists():
            raise forms.ValidationError("این شماره تلفن قبلا ثبت شده است!")

        if not phone.isdigit():
            raise forms.ValidationError('شماره تلفن باید فقط عدد باشد.')
        if not phone.startswith('09'):
            raise forms.ValidationError('شماره تلفن باید با 09 شروع شود.')
        if len(phone) != 11:
            raise forms.ValidationError('شماره تلفن باید 11 رقم باشد.')

        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'input__login__input'

        placeholders = {
            'phone': 'شماره تلفن همراه',
            'password': 'رمز عبور خود را وارد کنید',
            'password2': 'رمز عبور خود را تکرار کنید',
        }
        for field_name, placeholder in placeholders.items():
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['placeholder'] = placeholder


class UserEditForm(forms.ModelForm):
    class Meta:
        model = ShopUser
        fields = ['first_name', 'last_name', 'address']
        labels = {
            'first_name': 'نام',
            'last_name': 'نام خانوادگی',
            'address': 'آدرس',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all'
            })


class AccountEditForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['date_of_birth', 'id_card', 'payment_card_number', 'photo']
        labels = {
            'date_of_birth': 'تاریخ تولد',
            'id_card': 'کد ملی',
            'payment_card_number': 'شماره حساب بانکی',
            'photo': 'تصویر پروفایل',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field == 'photo':
                self.fields[field].widget.attrs.update({
                    'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
                })
            else:
                self.fields[field].widget.attrs.update({
                    'class': 'w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all'
                })


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['first_name', 'last_name', 'address_line', 'city', 'province', 'postal_code', 'phone']
        labels = {
            'first_name': 'نام گیرنده',
            'last_name': 'نام خانوادگی گیرنده',
            'address_line': 'آدرس کامل',
            'city': 'شهر',
            'province': 'استان',
            'postal_code': 'کد پستی',
            'phone': 'شماره تماس',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            # کلاس‌های Tailwind برای فرم‌های آدرس
            self.fields[field].widget.attrs.update({
                'class': 'w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all'
            })
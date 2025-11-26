from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import ShopUser, Account, Address


class ShopUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = ShopUser
        fields = ('phone', 'first_name', 'last_name', 'address', 'is_active', 'is_staff', 'is_superuser')

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')

        # بررسی وجود کاربر با این شماره (به جز خود کاربر)
        qs = ShopUser.objects.filter(phone=phone)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError('Phone number already in use.')

        # اعتبارسنجی فرمت شماره
        if not phone.isdigit():
            raise forms.ValidationError('Phone number must contain only digits.')
        if not phone.startswith('09'):
            raise forms.ValidationError('Phone number must start with 09.')
        if len(phone) != 11:
            raise forms.ValidationError('Phone number must be 11 digits.')

        return phone


class ShopUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = ShopUser
        fields = ('phone', 'first_name', 'last_name', 'address', 'is_active', 'is_staff', 'is_superuser')


    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if ShopUser.objects.filter(phone=phone).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Phone number already in use.')
        else:
            if ShopUser.objects.filter(phone=phone).exists():
                raise forms.ValidationError('Phone number already in use.')
        if not phone.isdigit():
            raise forms.ValidationError('Phone number must be entered in the format: 09999999999')
        if not phone.startswith('09'):
            raise forms.ValidationError('Phone number must be started in the format: 09')
        if len(phone) != 11:
            raise forms.ValidationError('Phone number must be 11 digits.')
        return phone


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        max_length=250,
        required=True,
        widget=forms.PasswordInput(),
        label='پسورد'
    )
    password2 = forms.CharField(
        max_length=250,
        required=True,
        widget=forms.PasswordInput(),
        label='تکرار پسورد'
    )

    class Meta:
        model = ShopUser
        fields = ['phone']
        widgets = {
            'phone': forms.TextInput(),
        }

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError("پسورد ها مطابقت ندارند!")
        return cd['password2']

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if ShopUser.objects.filter(phone=phone).exists():
            raise forms.ValidationError("این شماره تلفن قبلا ثبت شده است!")

        # اعتبارسنجی فرمت شماره
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

            # تعریف placeholder برای فیلدها
        placeholders = {
            'phone': 'شماره تلفن همراه',
            'password': 'رمز عبور خود را وارد کنید',
            'password2': 'رمز عبور خود را تکرار کنید',
        }

        # اضافه کردن placeholder به تمام فیلدها
        for field_name, placeholder in placeholders.items():
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



class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['first_name','last_name','address_line', 'city', 'province', 'postal_code', 'phone']
        widgets = {
            'address_line': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'province': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
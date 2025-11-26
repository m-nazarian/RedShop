from django import forms

class CheckoutAddressForm(forms.Form):
    first_name = forms.CharField(
        max_length=50,
        label='نام',
        widget=forms.TextInput(attrs={'placeholder': 'نام'})
    )
    last_name = forms.CharField(
        max_length=50,
        label='نام خانوادگی',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'نام خانوادگی'})
    )
    phone = forms.CharField(
        max_length=11,
        label='شماره تماس',
        widget=forms.TextInput(attrs={'placeholder': '09123456789'})
    )
    address = forms.CharField(
        label='آدرس',
        widget=forms.Textarea(attrs={'placeholder': 'آدرس کامل خود را وارد کنید'})
    )
    province = forms.CharField(
        max_length=100,
        label='استان',
        widget=forms.TextInput(attrs={'placeholder': 'تهران'})
    )
    city = forms.CharField(
        max_length=100,
        label='شهر',
        widget=forms.TextInput(attrs={'placeholder': 'تهران'})
    )
    postal_code = forms.CharField(
        max_length=10,
        label='کد پستی',
        widget=forms.TextInput(attrs={'placeholder': '1234567890'})
    )

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone.isdigit() or len(phone) != 11:
            raise forms.ValidationError('شماره تماس باید ۱۱ رقم و فقط عدد باشد.')
        return phone
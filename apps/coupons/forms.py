from django import forms



class CouponApplyForm(forms.Form):
    code = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'border border-gray-300 rounded-lg px-4 py-2 w-full text-sm focus:outline-none focus:border-blue-500',
            'placeholder': 'کد تخفیف را وارد کنید'
        }),
        label='کد تخفیف'
    )
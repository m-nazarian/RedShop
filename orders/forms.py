from django import forms

from .models import Order


class CheckoutPaymentForm(forms.Form):
    """روش پرداخت را در سمت سرور اعتبارسنجی می‌کند."""

    payment_method = forms.ChoiceField(
        choices=Order.PAYMENT_METHODS,
        label="روش پرداخت",
    )
from django.shortcuts import redirect
from django.contrib import messages

from django.views.decorators.http import require_POST

from .forms import CouponApplyForm
from .models import Coupon


@require_POST
def coupon_apply(request):
    """کد تخفیف معتبر و دارای ظرفیت مصرف را در سشن ذخیره می‌کند."""
    form = CouponApplyForm(request.POST)

    if form.is_valid():
        code = form.cleaned_data['code'].strip()

        coupon = (
            Coupon.usable_queryset()
            .filter(code__iexact=code)
            .first()
        )

        if coupon:
            request.session['coupon_id'] = coupon.id
            messages.success(request, f"کد تخفیف '{code}' با موفقیت اعمال شد.")
        else:
            request.session['coupon_id'] = None
            messages.error(request, "این کد تخفیف نامعتبر، منقضی یا مصرف‌شده است.")

    return redirect('cart:cart_detail')

from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import Coupon
from .forms import CouponApplyForm


@require_POST
def coupon_apply(request):
    """
    دریافت کد تخفیف، بررسی اعتبار و ذخیره در سشن
    """
    now = timezone.now()
    form = CouponApplyForm(request.POST)

    if form.is_valid():
        code = form.cleaned_data['code']
        try:
            # جستجو برای کوپن با شرایط اعتبار
            coupon = Coupon.objects.get(
                code__iexact=code,  # حساس نبودن به حروف بزرگ و کوچک
                valid_from__lte=now,  # تاریخ شروع قبل از الان باشد
                valid_to__gte=now,  # تاریخ انقضا بعد از الان باشد
                active=True  # تیک فعال بودن خورده باشد
            )

            # ✅ موفقیت: ذخیره در سشن
            request.session['coupon_id'] = coupon.id
            messages.success(request, f"کد تخفیف '{code}' با موفقیت اعمال شد.")

        except Coupon.DoesNotExist:
            # ❌ شکست: حذف کد قبلی (اگر بود) و نمایش خطا
            request.session['coupon_id'] = None
            messages.error(request, "این کد تخفیف نامعتبر یا منقضی شده است.")

    return redirect('cart:cart_detail')
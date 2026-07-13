
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import AccountEditForm, AddressForm, UserEditForm, UserRegistrationForm
from .models import Account, Address
from .security import LoginThrottle


def _safe_redirect_url(request, default_url_name, candidate=None):
    """Accept a return URL only when it points to the current host."""
    target = candidate or request.POST.get("next") or request.GET.get("next")

    if target and url_has_allowed_host_and_scheme(
        url=target,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return target

    return reverse(default_url_name)


@login_required
@require_GET
def profile(request):
    """Render the main account dashboard."""
    Account.objects.get_or_create(user=request.user)
    return render(request, "account/profile.html")


@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect("account:profile")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "ثبت‌نام با موفقیت انجام شد.")
            return redirect("account:login")
        messages.error(request, "اطلاعات واردشده را دوباره بررسی کنید.")
    else:
        form = UserRegistrationForm()

    return render(request, "registration/register.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def edit_account(request):
    user = request.user
    account, created = Account.objects.get_or_create(user=user)

    if request.method == "POST":
        user_form = UserEditForm(request.POST, instance=user)
        account_form = AccountEditForm(request.POST, request.FILES, instance=account)

        if user_form.is_valid() and account_form.is_valid():
            user_form.save()
            account_form.save()
            messages.success(request, "اطلاعات حساب ذخیره شد.")
            return redirect("account:profile")

        messages.error(request, "خطاهای فرم را بررسی کنید.")
    else:
        user_form = UserEditForm(instance=user)
        account_form = AccountEditForm(instance=account)

    return render(
        request,
        "registration/edit_account.html",
        {
            "user_form": user_form,
            "account_form": account_form,
            "created": created,
        },
    )


@require_http_methods(["GET", "POST"])
def user_login(request):
    if request.user.is_authenticated:
        return redirect("account:profile")

    if request.method == "POST":
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "")

        if LoginThrottle.is_blocked(request, phone):
            messages.error(
                request,
                "تعداد تلاش‌های ورود زیاد بوده است. چند دقیقه بعد دوباره تلاش کنید.",
            )
            return render(request, "account/login.html", status=429)

        user = authenticate(request, phone=phone, password=password)

        if user is not None:
            LoginThrottle.reset(request, phone)
            login(request, user)
            return redirect(_safe_redirect_url(request, "account:profile"))

        LoginThrottle.register_failure(request, phone)
        messages.error(request, "شماره تلفن یا رمز عبور نادرست است.")

    return render(request, "account/login.html")


@login_required
@require_POST
def user_logout(request):
    logout(request)
    return redirect("shop:index")


@login_required
@require_http_methods(["GET", "POST"])
def add_address(request):
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    if is_ajax:
        if request.method == "POST":
            form = AddressForm(request.POST)
            if form.is_valid():
                address = form.save(commit=False)
                address.user = request.user
                address.save()
                return JsonResponse({"success": True})

            html_form = render_to_string(
                "partials/address_form.html",
                {"form": form, "action_url": request.path},
                request=request,
            )
            return JsonResponse({"success": False, "html_form": html_form})

        form = AddressForm()
        html_form = render_to_string(
            "partials/address_form.html",
            {"form": form, "action_url": request.path},
            request=request,
        )
        return JsonResponse({"html_form": html_form})

    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            return redirect(_safe_redirect_url(request, "account:profile"))
    else:
        form = AddressForm()

    return render(request, "registration/add_address.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    if is_ajax:
        if request.method == "POST":
            form = AddressForm(request.POST, instance=address)
            if form.is_valid():
                form.save()
                return JsonResponse({"success": True})

            html_form = render_to_string(
                "partials/address_form.html",
                {"form": form, "action_url": request.path},
                request=request,
            )
            return JsonResponse({"success": False, "html_form": html_form})

        form = AddressForm(instance=address)
        html_form = render_to_string(
            "partials/address_form.html",
            {"form": form, "action_url": request.path},
            request=request,
        )
        return JsonResponse({"html_form": html_form})

    if request.method == "POST":
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, "آدرس ویرایش شد.")
            return redirect(_safe_redirect_url(request, "orders:checkout_address"))
    else:
        form = AddressForm(instance=address)

    return render(
        request,
        "registration/add_address.html",
        {"form": form, "is_edit": True},
    )


@login_required
@require_POST
def delete_address(request):
    address_id = request.POST.get("address_id")

    if address_id:
        address = get_object_or_404(Address, id=address_id, user=request.user)
        address.delete()
        messages.success(request, "آدرس حذف شد.")

    referer = request.META.get("HTTP_REFERER")
    return redirect(_safe_redirect_url(request, "orders:checkout_address", referer))


@login_required
@require_GET
def user_addresses_partial(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, "partials/addresses_list.html", {"addresses": addresses})


@login_required
@require_http_methods(["GET", "POST"])
def edit_profile_partial(request):
    user = request.user
    account, _ = Account.objects.get_or_create(user=user)

    if request.method == "POST":
        user_form = UserEditForm(request.POST, instance=user)
        account_form = AccountEditForm(request.POST, request.FILES, instance=account)

        if user_form.is_valid() and account_form.is_valid():
            user_form.save()
            account_form.save()
            return JsonResponse({"success": True})

        html_form = render_to_string(
            "partials/edit_profile.html",
            {"user_form": user_form, "account_form": account_form},
            request=request,
        )
        return JsonResponse({"success": False, "html_form": html_form})

    user_form = UserEditForm(instance=user)
    account_form = AccountEditForm(instance=account)

    return render(
        request,
        "partials/edit_profile.html",
        {"user_form": user_form, "account_form": account_form},
    )

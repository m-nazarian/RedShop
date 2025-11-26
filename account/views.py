from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .forms import *
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Account



@login_required
def profile(request):
    user = request.user
    if request.method == 'POST':
        form = ShopUserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('account:profile')
    else:
        form = ShopUserChangeForm(instance=user)

    return render(request, 'account/profile.html', {'form': form})



def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            messages.success(request, 'ثبت‌نام با موفقیت انجام شد ✅')
            return redirect('account:login')
        else:
            messages.error(request, 'خطایی در اطلاعات وارد شده وجود دارد ❌')
    else:
        form = UserRegistrationForm()

    return render(request, 'registration/register.html', {'form': form})


@login_required
def edit_account(request):
    user = request.user

    # اگر کاربر هنوز Account ندارد، ایجادش کن
    account, created = Account.objects.get_or_create(user=user)

    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=user)
        account_form = AccountEditForm(request.POST, request.FILES, instance=account)

        if user_form.is_valid() and account_form.is_valid():
            user_form.save()
            account_form.save()

            messages.success(request, 'اطلاعات شما با موفقیت ذخیره شد ✅')
            return redirect('account:profile')
        else:
            messages.error(request, 'لطفا خطاهای فرم را بررسی کنید ❌')

    else:
        user_form = UserEditForm(instance=user)
        account_form = AccountEditForm(instance=account)

    context = {
        'user_form': user_form,
        'account_form': account_form,
        'created': created,
    }

    return render(request, 'registration/edit_account.html', context)


def user_login(request):
    next_url = request.GET.get('next', 'cart:cart_detail')
    # اگر کاربر از قبل لاگین کرده
    if request.user.is_authenticated:
        return redirect('account:profile')

    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        user = authenticate(request, phone=phone, password=password)

        if user is not None:
            login(request, user)
            return redirect('account:profile')
        else:
            messages.error(request, 'شماره یا رمز عبور اشتباه است.')

    return render(request, 'account/login.html')


def user_logout(request):
    logout(request)
    return redirect('shop:index')


@login_required
def add_address(request):
    next_page = request.GET.get('next', 'account:profile')

    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            return redirect(next_page)
    else:
        form = AddressForm()

    return render(request, 'registration/add_address.html', {'form': form})


@login_required
def edit_address(request, address_id):
    # فقط کاربر صاحب آدرس بتواند آن را ویرایش کند
    address = get_object_or_404(Address, id=address_id, user=request.user)
    next_page = request.GET.get('next', 'orders:checkout_address')

    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, 'آدرس با موفقیت ویرایش شد.')
            return redirect(next_page)
    else:
        form = AddressForm(instance=address)

    return render(request, 'registration/add_address.html', {
        'form': form,
        'is_edit': True
    })


@login_required
@require_POST
def delete_address(request):
    address_id = request.POST.get('address_id')
    if address_id:
        address = get_object_or_404(Address, id=address_id, user=request.user)
        address.delete()
        messages.success(request, 'آدرس حذف شد.')

    return redirect(request.META.get('HTTP_REFERER', 'orders:checkout_address'))
from django.contrib.admin import AdminSite
from django.utils import timezone
from django.db.models import Sum, Count
from django.db.models.functions import TruncDay
from unfold.sites import UnfoldAdminSite
from orders.models import Order
from account.models import ShopUser
import datetime
import json


class RedShopAdminSite(UnfoldAdminSite):
    site_header = "RedShop Admin"
    site_title = "مدیریت فروشگاه ردشاپ"
    index_title = "داشبورد مدیریت"

    index_template = "admin/dashboard.html"

    def index(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}

        # 1. محاسبه KPI ها
        total_income = Order.objects.filter(paid=True).aggregate(Sum('total'))['total__sum'] or 0
        total_orders = Order.objects.count()
        total_users = ShopUser.objects.count()
        new_orders_count = Order.objects.filter(status='pending').count()

        def format_price(p):
            return f"{p:,}".replace(',', '،')

        kpi_data = [
            {
                "title": "درآمد کل",
                "metric": f"{format_price(total_income)} تومان",
                "footer": "مجموع فروش موفق",
            },
            {
                "title": "سفارشات جدید",
                "metric": str(new_orders_count),
                "footer": "منتظر بررسی",
            },
            {
                "title": "کاربران",
                "metric": str(total_users),
                "footer": "کل کاربران ثبت‌نامی",
            },
        ]

        # 2. چارت فروش
        today = timezone.now().date()
        last_7_days = today - datetime.timedelta(days=6)

        sales_data = (
            Order.objects.filter(paid=True, created__date__gte=last_7_days)
            .annotate(day=TruncDay('created'))
            .values('day')
            .annotate(total_sales=Sum('total'))
            .order_by('day')
        )

        sales_dict = {item['day'].date(): item['total_sales'] for item in sales_data}
        chart_labels = []
        chart_values = []

        days_map = {'Saturday': 'شنبه', 'Sunday': 'یکشنبه', 'Monday': 'دوشنبه', 'Tuesday': 'سه‌شنبه',
                    'Wednesday': 'چهارشنبه', 'Thursday': 'پنج‌شنبه', 'Friday': 'جمعه'}

        for i in range(7):
            date = last_7_days + datetime.timedelta(days=i)
            day_name = date.strftime("%A")
            chart_labels.append(days_map.get(day_name, day_name))
            chart_values.append(sales_dict.get(date, 0))

        performance_chart = {
            "title": "فروش ۷ روز گذشته",
            "type": "line",
            "labels": chart_labels,
            "datasets": [
                {
                    "label": "فروش (تومان)",
                    "data": chart_values,
                    "borderColor": "#3b82f6",
                    "backgroundColor": "rgba(59, 130, 246, 0.1)",
                    "fill": True,
                    "tension": 0.4,
                }
            ]
        }

        extra_context.update({
            "kpi": kpi_data,
            "chart": json.dumps(performance_chart, default=str),
        })

        return super().index(request, extra_context=extra_context)

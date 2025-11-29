from django import template
from ..models import CommentLike

register = template.Library()


@register.simple_tag
def get_user_reaction(comment, user):
    """
    بررسی می‌کند کاربر چه واکنشی به این نظر داشته است.
    خروجی: 'like', 'dislike', یا None
    """
    if not user.is_authenticated:
        return None

    try:
        # به جای کوئری مستقیم، از related_name استفاده می‌کنیم تا اگر prefetch شده باشد سریعتر باشد
        reaction = CommentLike.objects.get(comment=comment, user=user)
        return 'like' if reaction.status else 'dislike'
    except CommentLike.DoesNotExist:
        return None
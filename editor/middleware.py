from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.conf import settings
from .models import UserProfile

class UpdateLastActivityMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated:
            UserProfile.objects.filter(user=request.user).update(last_activity=timezone.now())
            print('Middle ware viewd')
        return None

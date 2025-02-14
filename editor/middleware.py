from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.conf import settings
from .models import UserProfile
import redis

class UpdateLastActivityMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated:
            UserProfile.objects.filter(user=request.user).update(last_activity=timezone.now())
            print('Middle ware viewd')
            redis_client = redis.StrictRedis(host='127.0.0.1', port=6379,db=0)


            try:
                print('redis_client_response',redis_client.ping())  # Should return True if connected
            except Exception as e:
                print(f"Error: {e}")
        return None

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import django

# Ensure this matches your project's name
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'realtime_code_editor.settings')

django.setup()
from editor import routing

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns
        )
    )
})

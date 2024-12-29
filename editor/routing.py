from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/ac/(?P<room_name>\w+)/$', consumers.CodeEditorConsumer.as_asgi()),
    re_path(r'ws/chat/(?P<chat_room>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/task-result/(?P<room_name>\w+)/$', consumers.TaskResult.as_asgi()),
    # ws/task-progress/<str:task_id>/
]

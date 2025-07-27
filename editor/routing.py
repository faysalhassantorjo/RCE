from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/ac/(?P<room_name>[-\w]+)/(?P<userprofile>\w+)$', consumers.CodeEditorConsumer.as_asgi()),

    re_path(r'ws/chat/(?P<chat_room>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/task-result/(?P<room_name>[-\w]+)/$', consumers.TaskResult.as_asgi()),
    re_path(r'ws/permission/(?P<room_name>[-\w]+)/$', consumers.PermissionConsumer.as_asgi()),

    re_path(r'ws/test-monitor/(?P<room_name>[-\w]+)/$', consumers.TestMonitor.as_asgi()),
    re_path(r'ws/global-chat/(?P<user>\w+)/$', consumers.GlobalChat.as_asgi()),
    re_path(r'ws/code-paste/(?P<room_name>[\w-]+)/(?P<userprofile>[\w-]+)/$', consumers.CopypasteConsumer.as_asgi()),
    re_path(r'ws/test-editor/', consumers.TestEditorConsumer.as_asgi()),
]

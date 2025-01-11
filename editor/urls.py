from django.urls import path, include
from .views import *
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('channel/<str:channel_id>/', channel, name='channel'),
    path('', home, name='home'),
    path('save-code/',save_file, name='save_code'),
    path('login/', auth_views.LoginView.as_view(template_name='editor/loginpage.html'), name='login'),
    path('logout/', logout_view, name='logout'),
     path('register/', register, name='register'),
    path('chat/<str:user_id>/', chat_room, name='chat_room'),
    path('create-channel/',create_channel, name='create_channel'),
    path('join-channel/<str:channel_id>/',join_channel,name='join_channel'),
    path('install-package/',install_package_view,name='install-package'),
    path('package/',package_install,name='package'),
    path('create-container/',create_container,name='create_container'),
    path('start-task/',start_task,name='start_task'),
    path('start-container/',start_container,name='start_container'),
    path('start-call/',start_call,name='start_call'),
]
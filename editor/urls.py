from django.urls import path, include
from .views import *
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('channel/<str:channel_id>/', channel, name='channel'),
    path('', home, name='home'),
    path('save-code/',save_file, name='save_code'),
    path('login/', auth_views.LoginView.as_view(template_name='editor/loginpage.html'), name='login'),
     path('logout/', logout_view, name='logout'),
]
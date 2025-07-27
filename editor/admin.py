from django.contrib import admin

from .models import *

# Register your models here.

admin.site.register(UserProfile)
admin.site.register(Channel)
admin.site.register(CodeFile)
admin.site.register(DMRoom)
admin.site.register(UserContainer)
admin.site.register(GlobalChatRoom)
admin.site.register(LabTest)
admin.site.register(AttemptTest)
admin.site.register(AttemptPaste)
from django.contrib import admin

# Register your models here.
from .models import Post, CodeBlock

admin.site.register(Post)
admin.site.register(CodeBlock)
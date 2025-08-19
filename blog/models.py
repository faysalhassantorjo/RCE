from django.db import models
from django.contrib.auth.models import User

LANGUAGE_CHOICES = [
    ('python', 'Python'),
    ('cpp', 'C++'),
    ('java', 'Java'),
]

from django.contrib.auth.models import User

class Post(models.Model):
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, default=1)  # default user id 1
    created_at = models.DateTimeField(auto_now_add=True)


class CodeBlock(models.Model):
    post = models.ForeignKey(Post, related_name="code_blocks", on_delete=models.CASCADE)
    language = models.CharField(
        max_length=20,
        choices=LANGUAGE_CHOICES,
        blank=False,
        null=False
    )
    code = models.TextField()

    def __str__(self):
        return f"{self.language} code for post: {self.post.title}"

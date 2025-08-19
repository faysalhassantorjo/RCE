from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Post, CodeBlock


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "password1", "password2", "email"]


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'description']  # added description field
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Write a brief description about your post...'
            }),
        }


class CodeBlockForm(forms.ModelForm):
    class Meta:
        model = CodeBlock
        fields = ['language', 'code']
        widgets = {
            'code': forms.Textarea(attrs={
                'rows': 10,
                'cols': 80,
                'placeholder': 'Write your code here...'
            }),
        }

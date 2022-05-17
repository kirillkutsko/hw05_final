from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("text", "group", "image")
        labels = {
            "text": "Текст",
            "group": "Группа",
        }
        help_texts = {
            "text": "Напишите текст поста",
            "group": "Выберите группу",
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)
        labels = {
            "text": "Текст",
        }
        help_texts = {
            "text": "Напишите текст комментария",
        }

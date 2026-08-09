from django import forms
from django.core.exceptions import ValidationError

from .models import Comment, Post


class StyledForm(forms.ModelForm):
    """Drops the ':' Django puts after every label — the CSS uses small caps."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super().__init__(*args, **kwargs)


class PostForm(StyledForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'featured_image', 'category', 'author']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Give it a headline worth clicking'}),
            'content': forms.Textarea(attrs={
                'rows': 14,
                'placeholder': 'Start writing. Blank lines make new paragraphs.',
            }),
            'author': forms.TextInput(attrs={'placeholder': 'Who wrote this?'}),
        }
        help_texts = {
            'title': 'The URL or slug is auto-generated from the title.',
            'featured_image': 'Optional. Leave it alone and the house cover is used.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].empty_label = 'Choose a section'

    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        if len(title) < 5:
            raise ValidationError('Use a real title.')
        return title


class CommentForm(StyledForm):
    class Meta:
        model = Comment
        fields = ['name', 'content']
        labels = {
            'name': 'Your name',
            'content': 'Your comment',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Who is writing?',
                'autocomplete': 'name',
            }),
            'content': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Say something worth reading.',
            }),
        }

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if len(name) < 2:
            raise ValidationError('That name is too short to be a name.')
        return name

    def clean_content(self):
        content = self.cleaned_data['content'].strip()
        if len(content) < 5:
            raise ValidationError('Write a little more than that.')
        return content

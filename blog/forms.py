"""Forms.

A ModelForm is the shortest honest path from an HTML form to a saved row: it
reads the model, builds the fields, validates them, and writes them back. What
it cannot know is anything about *this* site's rules — that a title has to be
a real title, that only an editor may publish someone else's work. Those go in
`clean_*()` methods and in the form's `__init__`.
"""

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
        fields = ['title', 'content', 'featured_image', 'category', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Give it a headline worth clicking'}),
            'content': forms.Textarea(attrs={
                'rows': 14,
                'placeholder': 'Start writing. Blank lines make new paragraphs.',
            }),
        }
        help_texts = {
            'title': 'The URL or slug is auto-generated from the title.',
            'featured_image': 'Optional. Leave it alone and the house cover is used.',
            'status': 'Drafts are visible to you and the editors. Nobody else.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].empty_label = 'Choose a section'

    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        if len(title) < 5:
            raise ValidationError('Use a real title.')
        return title

    def clean_content(self):
        content = self.cleaned_data['content'].strip()
        if len(content.split()) < 20:
            raise ValidationError('Twenty words minimum. This is a magazine, not a status update.')
        return content


class CommentForm(StyledForm):
    """No name field any more.

    The commenter is `request.user`, set in the view. A field the browser can
    send is a field the browser can lie about, so identity never travels
    through the form.
    """

    class Meta:
        model = Comment
        fields = ['content']
        labels = {'content': 'Your comment'}
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Say something worth reading.',
            }),
        }

    def clean_content(self):
        content = self.cleaned_data['content'].strip()
        if len(content) < 5:
            raise ValidationError('Write a little more than that.')
        return content

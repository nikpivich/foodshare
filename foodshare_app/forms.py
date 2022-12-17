from django import forms

from .models import Post


class PostForm(forms.Form):
    title = forms.CharField(label='Заголовок', required=True, max_length=100)
    image = forms.ImageField(required=False)
    content = forms.CharField(label='Содержание', required=True, max_length=100)


class PostModelForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'image', 'content']

        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.TextInput(attrs={'class': 'form-control'})
        }
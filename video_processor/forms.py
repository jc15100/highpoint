from django import forms
from .models import Video
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class RegisterUserForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

class UploadForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ('filesystem_url', )
    user = forms.HiddenInput()

    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id', None)
        super(UploadForm, self).__init__(*args, **kwargs)

        if user_id:
            self.user = user_id

class DownloadLinkForm(forms.ModelForm):
    class Meta:
        model= Video
        fields = ('web_url',)
    user = forms.HiddenInput()

    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id', None)
        super(DownloadLinkForm, self).__init__(*args, **kwargs)

        if user_id:
            self.user = user_id
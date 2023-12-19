from django import forms
from .models import Video

class UploadForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ('location', )
    user = forms.HiddenInput()

    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id', None)
        super(UploadForm, self).__init__(*args, **kwargs)

        if user_id:
            self.user = user_id

class DownloadLinkForm(forms.ModelForm):
    class Meta:
        model= Video
        fields = ('video_url',)
    user = forms.HiddenInput()

    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id', None)
        super(DownloadLinkForm, self).__init__(*args, **kwargs)

        if user_id:
            self.user = user_id
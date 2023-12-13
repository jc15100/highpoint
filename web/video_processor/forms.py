from django import forms
from .models import Video

class UploadForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ('location',)

class DownloadLinkForm(forms.ModelForm):
    class Meta:
        model= Video
        fields = ('video_url',)
from django import forms
from .models import Video

class UploadForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ('location',)
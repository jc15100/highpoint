import os
import logging
logging.basicConfig()
logger = logging.getLogger('django')

from django.http import JsonResponse
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings

from .models import Video, Userprofile
from .forms import UploadForm, DownloadLinkForm
from .services.engine import Engine
from .services.youtube_helper import YoutubeHelper

# Global variables for services
engine = Engine()
youtube = YoutubeHelper()

def uploader(request):
    uploadForm = UploadForm()
    downloadLinkForm = DownloadLinkForm()
    return render(request, 'upload-page.html', {'form_upload': uploadForm, 'form_link': downloadLinkForm})

def frontpage(request):
    return render(request, 'frontpage.html')

def download_link(request):
    if request.method == "POST":
        form = DownloadLinkForm(request.POST)
        if form.is_valid():
            video = form.save()
            video_url = video.video_url
            
            output_path = str(settings.MEDIA_ROOT)
            video_path = youtube.download_link(str(video_url), output_path)
            
            logger.info("Results path " + str(output_path))
            results = engine.process(video_path, output_path)
            return JsonResponse({'success': True, 'results': results})
        else:
            logger.error("Form not valid, skipping save")
            return JsonResponse({'success': False, 'results': []})

def upload(request):
    if request.FILES:
        form = UploadForm(request.POST, request.FILES)

        if form.is_valid():
            video = form.save()
            
            video_path = str(settings.BASE_DIR) + str(video.location.url)
            output_path = str(settings.MEDIA_URL)

            logger.info("Input path " + str(video_path))
            logger.info("Results path " + str(output_path))

            results = engine.process(video_path, output_path)
            return JsonResponse({'success': True, 'results': results})
        else:
            logger.error("Form not valid, skipping save")
            return JsonResponse({'success': False, 'results': []})

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            userprofile = Userprofile.objects.create(user=user)
            return redirect('frontpage')
    else:
        form = UserCreationForm()
    
    return render(request, 'signup.html', {'form': form})

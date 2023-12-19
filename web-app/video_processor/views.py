import os
import logging
import json

logging.basicConfig()
logger = logging.getLogger('django')

from django.http import JsonResponse
from django.core.serializers import serialize
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import login, get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings

from .models import Video
from .serializers import VideoSerializer
from .forms import UploadForm, DownloadLinkForm
from .services.engine import Engine
from .services.youtube_helper import YoutubeHelper

# Global variables for services
engine = Engine()
youtube = YoutubeHelper()

def upload_page(request):
    uploadForm = UploadForm(user_id=request.user.id)
    
    downloadLinkForm = DownloadLinkForm(user_id=request.user.id)
    return render(request, 'upload-page.html', {'form_upload': uploadForm, 'form_link': downloadLinkForm})

def homepage(request):
    return render(request, 'homepage.html')

def user_content(request):
    if request.method == "GET":
        if request.user.is_authenticated == True:
            User = get_user_model()
            print("Current user " + str(request.user))
            videos = Video.objects.filter(user=User.objects.get(username=request.user))
            print("Total videos uploaded " + str(len(videos)))

            serializer = VideoSerializer(videos, many=True)
            serialized_data = serializer.data
            return JsonResponse({'success': True, 'content': serialized_data})
        else:
            print("User not logged in")
            return JsonResponse({'success': True, 'content': []})

def download_link(request):
    if request.method == "POST":
        form = DownloadLinkForm(request.POST)
        if form.is_valid():
            # add user to form
            form.instance.user = request.user
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
            # add user to form
            form.instance.user = request.user
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

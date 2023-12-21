import os
import logging
import json

from django.http import JsonResponse
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import login, get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings

from .models import Video, UserProfile
from .serializers import VideoSerializer, UserProfileSerializer
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
            videos = Video.objects.filter(user=User.objects.get(username=request.user), type=Video.VideoTypes.RAW)
            profile = UserProfile.objects.get(user=User.objects.get(username=request.user))

            video_serializer = VideoSerializer(videos, many=True)
            serialized_videos = video_serializer.data

            profile_serializer = UserProfileSerializer(profile)
            serialized_profile = profile_serializer.data

            return JsonResponse({'success': True, 'videos': serialized_videos, 'profile': serialized_profile})
        else:
            print("User not logged in")
            return JsonResponse({'success': True, 'videos': [], 'profile': ''})

def download_link(request):
    if request.method == "POST":
        form = DownloadLinkForm(request.POST)
        if form.is_valid():
            form.instance.user = request.user
            video = form.save()

            web_url = video.web_url
            
            output_path = str(settings.MEDIA_ROOT)
            video_path = youtube.download_link(str(web_url), output_path)
            
            print("Results path " + str(output_path))
            results = engine.process(video_path, output_path)
            
            update_user_profile(request, results)

            return JsonResponse({'success': True, 'results': results})
        else:
            print("Form not valid, skipping save")
            return JsonResponse({'success': False, 'results': []})

def upload(request):
    if request.FILES:
        form = UploadForm(request.POST, request.FILES)

        if form.is_valid():
            # add user to form
            form.instance.user = request.user
            video = form.save()
            
            video_path = str(settings.BASE_DIR) + str(video.filesystem_url.url)
            output_path = str(settings.MEDIA_ROOT)

            print("Input path " + str(video_path))
            print("Results path " + str(output_path))

            results = engine.process(video_path, output_path)
                        
            update_user_profile(request, results)

            return JsonResponse({'success': True, 'results': results})
        else:
            print("Form not valid, skipping save")
            return JsonResponse({'success': False, 'results': []})

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            userprofile = UserProfile.objects.create(user=user)
            userprofile.save()
            return redirect('frontpage')
    else:
        form = UserCreationForm()
    
    return render(request, 'signup.html', {'form': form})

# Private methods, helpers

def update_user_profile(request, results):
    print("Updating user profile for " + str(request.user))
    if results["supported"] == True:
        User = get_user_model()
        user_auth = User.objects.get(username=request.user) 
        user = UserProfile.objects.get(user=user_auth)
        user.number_of_uploads += 1

        # TODO: Calculate level based on AI inputs
        user.level = round(((1 / user.number_of_uploads) * 0.2) + user.level, 2)
        user.players += 4

        for smash_file in results["smashes"]:
            print(smash_file)
            smash = Video.objects.create(filesystem_url=smash_file, type=Video.VideoTypes.SMASH, user=user_auth)
            user.smashes.add(smash)

        for highlight_file in [results["group_highlight"]]:
            print(highlight_file)
            highlight = Video.objects.create(filesystem_url=highlight_file, type=Video.VideoTypes.HIGHLIGHT, user=user_auth)
            user.highlights.add(highlight)

        user.save()
        print("Profile updated for " + str(request.user))
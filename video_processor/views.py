import json
import logging

from django.http import JsonResponse
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import login, get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings

from .models import Video, UserProfile
from .serializers import VideoSerializer, UserProfileSerializer
from .forms import UploadForm, DownloadLinkForm
from .services.highpoint import HighpointService
from .services.youtube_helper import YoutubeHelper

# Global variables for services
highpoint = HighpointService()
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
            print("Current user: " + str(request.user))
            videos = Video.objects.filter(user=User.objects.get(username=request.user), type=Video.VideoTypes.RAW)
            profile = UserProfile.objects.get(user=User.objects.get(username=request.user))

            highpoint.renew_user_content(videos, profile)

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
            # check if user has reached free quota
            user = _get_user_profile(request)
            if user.number_of_uploads > settings.FREE_QUOTA:
                print("User has reached free quota, returning")
                results = json.dumps({'trial_done': True})
            else:
                # add user to form & save video object in storage
                form.instance.user = request.user
                video = form.save()
                print("Link saved to storage")

                web_url = video.web_url
                
                # download Youtube video locally and add to video
                output_path = str(settings.MEDIA_ROOT)
                video.filesystem_url = youtube.download_link(str(web_url), output_path)

                if video.filesystem_url is not None:
                    results = highpoint.process(request)
                    return JsonResponse({'success': True, 'results': results})
                else:
                    return JsonResponse({'success': False, 'results': json.dumps([])})
        else:
            print("Form not valid, skipping save")
            return JsonResponse({'success': False, 'results': []})

def upload_url(request):
    user = _get_user_profile(request)
    if user.number_of_uploads > settings.FREE_QUOTA:
        print("User has reached free quota, returning")
        return JsonResponse({'trial_done': True})
    else:
        test_url = highpoint.upload_signed_url(request)
        return JsonResponse({'url': test_url})

def process(request):
    result = highpoint.process(request.user, request.body)
    return JsonResponse({'success': True, 'results': result.__dict__})

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            logging.info("About to save UserProfile for " + str(user))
            try:
                userprofile = UserProfile.objects.create(user=user)
                userprofile.save()
            except Exception as e:
                logging.error("Failed to save user profile with exception " + str(e)) 
            return redirect('homepage')
    else:
        form = UserCreationForm()
    
    return render(request, 'signup.html', {'form': form})

# MARK: Private methods

def _get_user_profile(request):
    User = get_user_model()
    user_auth = User.objects.get(username=request.user) 
    user_p = UserProfile.objects.get(user=user_auth)
    return user_p
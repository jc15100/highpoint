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
from .services.engine import Engine
from .services.youtube_helper import YoutubeHelper
from .services.storage_helper import StorageHelper

# Global variables for services
engine = Engine()
youtube = YoutubeHelper()
storage_helper = StorageHelper()

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

            _renew_user_content(videos, profile)

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
                    results = engine.process(video, output_path, request)
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
        body = json.loads(request.body)
        fileName = body['fileName']
        fileType = body['fileType']
        storage_bucket = storage_helper.get_storage_bucket_path(request.user, fileName)

        test_url = storage_helper.get_signed_url_for_upload(storage_bucket, fileType, "PUT")
        print("URL signed " + str(test_url))
        return JsonResponse({'url': test_url})

def upload(request):
    if request.FILES:
        form = UploadForm(request.POST, request.FILES)
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
                print("Video saved to storage")

                results = engine.process(video, str(settings.MEDIA_ROOT), request)

            return JsonResponse({'success': True, 'results': results})
        else:
            print("Form not valid, skipping save")
            return JsonResponse({'success': False, 'results': []})

def process(request):
    result = engine.process(request, output_path=str(settings.MEDIA_ROOT))
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

def _renew_user_content(videos: [Video], profile: UserProfile):
    print("Renewing ({}) Raw Videos".format(len(videos)))

    for video in videos:
        url = storage_helper.get_signed_url(str(video.filesystem_url), "GET")
        video.web_url = url
    
    print("Renewing ({}) Smash Videos".format(len(profile.smashes.all())))
    for smash in profile.smashes.all():
        smash_url = storage_helper.get_signed_url(str(smash.filesystem_url), "GET")
        smash.web_url = smash_url
    
    print("Renewing ({}) Highlight Videos".format(len(profile.highlights.all())))
    for highlight in profile.highlights.all():
        highlight_url = storage_helper.get_signed_url(str(highlight.filesystem_url), "GET")
        highlight.web_url = highlight_url
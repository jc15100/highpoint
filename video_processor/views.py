import tempfile
import os

from django.http import JsonResponse
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import login, get_user_model
from django.core.files.storage import FileSystemStorage, default_storage
from django.core.files.base import ContentFile
from django.core.files import File
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
local_storage = FileSystemStorage()
local_storage.base_location = settings.MEDIA_ROOT

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
            
            process_results(request, results)

            return JsonResponse({'success': True, 'results': results})
        else:
            print("Form not valid, skipping save")
            return JsonResponse({'success': False, 'results': []})

def upload(request):
    if request.FILES:
        form = UploadForm(request.POST, request.FILES)

        if form.is_valid():
            # add user to form & save video object in storage
            form.instance.user = request.user
            print("Saving file to Google Cloud storage")
            video = form.save()
            print("Video saved to storage")

            # get local copy for processing
            local_file_path = save_video_locally(video)
            results = engine.process(local_file_path, str(settings.MEDIA_ROOT))
                        
            process_results(request, results)
            return JsonResponse({'success': True, 'results': []})#results})
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

def save_video_locally(video):
    # Download file to local filesystem & process it.
    # If the file is not on local storage download it
    print("Saving temp video locally")
    filename = video.filesystem_url.name
    if not local_storage.exists(filename):
        filecontent = video.filesystem_url.read()
        local_storage.save(filename, ContentFile(filecontent))
            
    local_file_path = local_storage.path(filename)
    return local_file_path

def save_video_remotely(user, video_path):
    # temp_file is to avoid SuspiciousFileOperation while saving from file path
    temp_file = tempfile.NamedTemporaryFile(dir='media')
    video = open(video_path, 'rb')
    temp_file.write(video.read())

    # store in default_storage (GCloud)
    storage_path = "results/" + str(user) + "/" + os.path.basename(video_path)
    print("Storing at " + str(storage_path))
    path = default_storage.save(storage_path, File(temp_file))
    print("Stored at " + str(default_storage.url(path)))

def process_results(request, results):
    print("Updating user profile in DB & results in storage for " + str(request.user))
    if results["supported"] == True:
        User = get_user_model()
        user_auth = User.objects.get(username=request.user) 
        user = UserProfile.objects.get(user=user_auth)
        user.number_of_uploads += 1

        # TODO: redo formula for user level considering more than just smashes
        user.level = round(((1 / len(user.smashes.all())) * 0.2) + user.level, 2)
        user.players += 4

        for smash_file in results["smashes"]:
            # store in Google Cloud
            save_video_remotely(request.user, smash_file)

            # store in DB
            smash = Video.objects.create(filesystem_url=smash_file, type=Video.VideoTypes.SMASH, user=user_auth)
            user.smashes.add(smash)

        for highlight_file in [results["group_highlight"]]:
            # store in Google Cloud
            save_video_remotely(request.user, highlight_file)

            # store in DB
            highlight = Video.objects.create(filesystem_url=highlight_file, type=Video.VideoTypes.HIGHLIGHT, user=user_auth)
            user.highlights.add(highlight)

        user.save()
        print("Profile updated for " + str(request.user))
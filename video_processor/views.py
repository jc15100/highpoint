import json
import logging
import datetime

from django.http import JsonResponse
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import login, get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings

from google.cloud import storage
from google.cloud.storage._signing import generate_signed_url_v4

from .models import Video, UserProfile
from .serializers import VideoSerializer, UserProfileSerializer
from .forms import UploadForm, DownloadLinkForm
from .services.engine import Engine
from .services.youtube_helper import YoutubeHelper
from ml.pipeline.result import HighpointResult

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
            print("Current user: " + str(request.user))
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
        return JsonResponse(json.dumps({'trial_done': True}))
    else:
        body = json.loads(request.body)
        fileName = body['fileName']
        fileType = body['fileType']
        storage_bucket = _get_storage_bucket_path(request.user, fileName)

        test_url = _get_signed_url_for_upload(storage_bucket, fileType, "PUT")
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
    body = json.loads(request.body)
    fileName = body['fileName']

    blob_path = _get_storage_bucket_path(request.user, fileName)
    local_path = _get_local_copy(request.user, blob_path)

    print("Local path: " + str(local_path))

    result = engine.process(local_path, str(settings.MEDIA_ROOT), request)
    result = _hydrate_results(request, result=result)

    return JsonResponse({'success': True, 'results': result})

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

def _hydrate_results(request, result: HighpointResult):
    result.group_highlight = _get_signed_url(result.group_highlight, "GET")
    return result.__dict__

def _get_user_profile(request):
    User = get_user_model()
    user_auth = User.objects.get(username=request.user) 
    user_p = UserProfile.objects.get(user=user_auth)
    return user_p

def _get_storage_client():
    return storage.Client.from_service_account_json(settings.CREDENTIALS_JSON)

def _get_canonical_path(sub_bucket):
    return "/" + settings.GS_BUCKET_NAME + "/" + sub_bucket

def _get_storage_bucket_path(user, filename):
    return "media" + "/{}/".format(user) + filename

def _get_results_bucket_path(user, filename):
    return "results" + "/{}/".format(user) + filename

def _get_local_copy(user, blob_path):
    client = _get_storage_client()
    bucket_name = settings.GS_BUCKET_NAME
    bucket = client.get_bucket(bucket_name)
    video_blob = bucket.blob(blob_path)

    local_video_path = str(settings.MEDIA_ROOT) + "/{}_local_video.mp4".format(str(user))
    video_blob.download_to_filename(local_video_path)
    return local_video_path

def _get_signed_url_for_upload(sub_bucket, content_type, method):
    client = _get_storage_client()
    expiration = datetime.timedelta(minutes=15)
    canonical_resource = _get_canonical_path(sub_bucket)

    url = generate_signed_url_v4(
        client._credentials,
        resource=canonical_resource,
        api_access_endpoint=settings.API_ACCESS_ENDPOINT,
        expiration=expiration,
        method=method,
        content_type=content_type
    )

    print("generated signed url " + str(url))
    return url

def _get_signed_url(sub_bucket, method):
    client = _get_storage_client()
    expiration = datetime.timedelta(minutes=15)
    canonical_resource = _get_canonical_path(sub_bucket)

    url = generate_signed_url_v4(
        client._credentials,
        resource=canonical_resource,
        api_access_endpoint=settings.API_ACCESS_ENDPOINT,
        expiration=expiration,
        method=method
    )

    print("generated signed url " + str(url))
    return url

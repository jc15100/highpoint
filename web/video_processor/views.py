import os
import logging
logging.basicConfig()
logger = logging.getLogger('django')

from django.http import HttpResponse
from rest_framework.parsers import JSONParser
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings

from .models import Video, Userprofile
from .serializers import VideoSerializer
from .forms import UploadForm
from .engine import Engine

engine = Engine()

def uploader(request):
    form = UploadForm()
    return render(request, 'upload-page.html', {'form': form})

def frontpage(request):
    return render(request, 'frontpage.html')

def upload(request):
    if request.FILES:
        form = UploadForm(request.POST, request.FILES)

        if form.is_valid():
            video = form.save()
            
            video_path = str(settings.BASE_DIR) + str(video.location.url)
            output_path = str(settings.MEDIA_URL)

            logger.info("Input path " + str(video_path))
            logger.info("Results path " + str(output_path))

            segments = engine.process(video_path, output_path)
            return JsonResponse({'success': True, 'segments': segments})
        else:
            logger.error("Form not valid, skipping save")
            return JsonResponse({'success': False, 'segments': []})

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

@csrf_exempt
def video(request):
    if (request.method == 'GET'):
        videos = Video.objects.all()
        serializer = VideoSerializer(videos, many=True)
        return JsonResponse(serializer.data, safe=False)
    elif (request.method == 'POST'):
        data = JSONParser().parse(request)
        serializer = VideoSerializer(data=data)

        if (serializer.is_valid()):
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)

@csrf_exempt
def video_detail(request, pk):
    try:
        video = Video.objects.get(pk=pk)
    except:
        return HttpResponse(status=404)
    if (request.method == 'PUT'):
        data = JSONParser().parse(request)
        serializer = VideoSerializer(video, data=data)
        if (serializer.is_valid()):
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, 400)
    elif (request.method == 'DELETE'):
        video.delete()
        return HttpResponse(stauts=204)
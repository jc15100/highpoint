from django.http import HttpResponse
from rest_framework.parsers import JSONParser
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from .serializers import VideoSerializer

from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm

from .models import Video, Userprofile
from django.views.generic import TemplateView
from .forms import UploadForm

def uploader(request):
    form = UploadForm()
    return render(request, 'upload-page.html', {'form': form})

def frontpage(request):
    return render(request, 'frontpage.html')

def upload(request):
    if request.FILES:
        form = UploadForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
        else:
            print("Form not valid, skipping save")
    
    return JsonResponse({'success': True})

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
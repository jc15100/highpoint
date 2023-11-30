from django.http import HttpResponse
# parsing data from the client
from rest_framework.parsers import JSONParser
# To bypass having a CSRF token
from django.views.decorators.csrf import csrf_exempt
# for sending response to the client
from django.http import HttpResponse, JsonResponse
# API definition for task
from .serializers import VideoSerializer
# Task model
from .models import Video
from django.views.generic import TemplateView

class HomeView (TemplateView):
    template_name = "home.html"

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
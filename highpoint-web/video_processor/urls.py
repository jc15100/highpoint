from django.urls import path

from video_processor.views import *
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload, name='upload'),
    path("get-video/", views.video),
]
from django.urls import path

from video_processor.views import *
from . import views

urlpatterns = [
    path('', HomeView.as_view(), name='homepage'),
    path("get-video/", views.video),
    path("get-video/<int:pk>/", views.video_detail)
]
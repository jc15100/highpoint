from django.urls import path
from django.contrib.auth import views as djviews
from django.conf.urls.static import static
from django.conf import settings

from video_processor.views import *
from . import views

urlpatterns = [
    path('', views.frontpage, name='frontpage'),
    path('uploader', views.uploader, name='uploader'),
    path('upload/', views.upload, name='upload'),
    path('download_link/', views.download_link, name='download_link'),
    path('signup/', views.signup, name='signup'),
    path('login/', djviews.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', djviews.LogoutView.as_view(), name='logout'),
] + static(settings.MEDIA_URL, document_root= settings.MEDIA_ROOT)
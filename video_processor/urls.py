from django.urls import path, re_path, include
from django.contrib.auth import views as djviews
from django.conf.urls.static import static
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from video_processor.views import *
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('user_content/', views.user_content, name='user_content'),

    path('uploader', views.upload_page, name='uploader'),
    path('upload_url/', views.upload_url, name='upload_url'),

    path('dispatch/', views.dispatch, name="dispatch"),
    path('process_task/', csrf_exempt(views.process_task), name="process_task"),

    path('task_status/', views.task_status, name="task_status"),
    path('fetch_results/', views.fetch_results, name="fetch_results"),

    path('download_link/', views.download_link, name='download_link'),

    path('plans/', views.plans, name='plans'),
    path('subscribe/', views.subscribe, name='subscribe'),
    path('cancel/', views.cancel_subscription, name='cancel_subscription'),

    path('cleanup/', csrf_exempt(views.cleanup), name="cleanup"),

    path('signup/', views.signup, name='signup'),
    path('login/', djviews.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', djviews.LogoutView.as_view(), name='logout'),

    path(r'^_ah/warmup$', views.warmup, name='warmup'),
] + static(settings.MEDIA_URL, document_root= settings.MEDIA_ROOT)
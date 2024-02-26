import json
import logging
import djstripe
import stripe

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from .models import Video, UserProfile, Task
from .serializers import VideoSerializer, UserProfileSerializer
from .forms import UploadForm, DownloadLinkForm
from .services.highpoint import HighpointService
from .services.youtube_helper import YoutubeHelper
from .tasks import create_task

from django.views import View
from djstripe.models import Product

# Global variables for services
highpoint = HighpointService()
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

            highpoint.renew_user_content(videos, profile)

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
            user = _get_user_profile(request.user)
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
                    results = highpoint.process(request)
                    return JsonResponse({'success': True, 'results': results})
                else:
                    return JsonResponse({'success': False, 'results': json.dumps([])})
        else:
            print("Form not valid, skipping save")
            return JsonResponse({'success': False, 'results': []})

def upload_url(request):
    user = _get_user_profile(request.user)
    if user.number_of_uploads > settings.FREE_QUOTA:
        print("User has reached free quota, returning")
        return JsonResponse({'trial_done': True})
    else:
        test_url = highpoint.upload_signed_url(request)
        #user.number_of_uploads += 1
        #user.save()
        return JsonResponse({'url': test_url})

def process(request):
    payload = {}
    payload["user"] = request.user.username
    body = json.loads(request.body)
    payload["fileName"] = body["fileName"]

    response = create_task(url="/process_task/", payload=payload)
    return JsonResponse({'success': True, 'task': "test-task"})

@csrf_exempt
def process_task(request):
    current_task_id = request.headers['X-AppEngine-TaskName']
    logging.info("Request received for task {}".format(current_task_id))

    payload = request.body.decode('utf-8')
    logging.info("Reached process_task!")
    logging.info("Reached task with payload {}".format(payload))
    
    payload_json = json.loads(payload)
    user = payload_json["user"]
    fileName = payload_json["fileName"]

    highpoint = HighpointService()
    length = highpoint.estimate_time(fileName)

    user_profile = _get_user_profile(payload_json["user"])
    task_in_progress = Task.objects.create(task_identifier=current_task_id, is_done=False, progress=length, user=user_profile.user)   
    user_profile.tasks_in_progress.add(task_in_progress)
    user_profile.save()
    
    highpoint.process(user, fileName)

    return HttpResponse('OK')

# Eventually replace with WebSockets
def task_status(request):
    user_profile = _get_user_profile(request.user)

    tasks: [Task] = user_profile.tasks_in_progress.all()
    status = {}

    for task_in_progress in tasks:
        # we are checking every 10 seconds
        progress_ticks = task_in_progress.progress / 10
        current_progress = 100 / progress_ticks
        status[task_in_progress.task_identifier] = current_progress
        task_in_progress.progress = task_in_progress.progress * (current_progress + current_progress)
        task_in_progress.save()
    
    user_profile.save()
    return JsonResponse({'success': True, 'tasks': status})

@login_required
def subscription(request):
    # products = Product.objects.all()

    # context = {
    #     'products': products
    # }

    return render(request, 'subscription.html', {'products': []})

@login_required
def create_sub(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        payment_method = data['payment_method']
        stripe.api_key = djstripe.settings.STRIPE_SECRET_KEY

        payment_method_obj = stripe.PaymentMethod.retrieve(payment_method)
        djstripe.models.PaymentMethod.sync_from_stripe_data(payment_method_obj)

        try:
            customer = stripe.Customer.create(
                payment_method=payment_method,
                email=request.user.email,
                invoice_settings={
                    'default_payment_method': payment_method
                }
            )

            djstripe_customer = djstripe.models.Customer.sync_from_stripe_data(customer)

            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[
                    {
                        "price": data["price_id"]
                    }
                ],
                expand=["latest_invoice.payment_intent"]
            )

            djstripe_subscription = djstripe.models.Subscription.sync_from_stripe_data(subscription)

            request.user.userprofile.subscription = subscription.id
            request.user.userprofile.save()

            return JsonResponse(subscription)
        except Exception as e:
            return JsonResponse({'error': (e.args[0])}, status=403)
    else:
        return HttpResponse('Request method not allowed')

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

def _get_user_profile(user):
    User = get_user_model()
    user_auth = User.objects.get(username=user) 
    user_p = UserProfile.objects.get(user=user_auth)
    return user_p
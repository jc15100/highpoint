import json
import logging
import djstripe
import stripe
from datetime import datetime, timedelta, timezone

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.gis.geoip2 import GeoIP2

from djstripe.models import Product, Subscription

from .models import Video, UserProfile, Task, TaskResult, Image
from .serializers import VideoSerializer, UserProfileSerializer
from .forms import UploadForm, DownloadLinkForm, RegisterUserForm
from .services.highpoint import HighpointService
from .services.youtube_helper import YoutubeHelper
from .tasks import create_task

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
            print("Current user: " + str(request.user))
            user = get_user_model().objects.get(username=request.user)

            videos = Video.objects.filter(user=user, type=Video.VideoTypes.RAW)
            profile = _get_user_profile(request.user)

            highpoint.renew_user_content(videos, profile)

            # find all task results, group by date, extract stats
            task_results = TaskResult.objects.filter(user=user)

            print("Found profile for {} with {} uploads & {} task_results".format(profile.user, profile.number_of_uploads, len(task_results.all())))

            graph_data = []
            data_by_date = {}
            for task_result in task_results.all():
                if task_result.timestamp in data_by_date:
                    data_by_date[task_result.timestamp].append(len(task_result.smashes.all()))
                else:
                    data_by_date[task_result.timestamp] = [len(task_result.smashes.all())]

            for timestamp, smash_counts in data_by_date.items():
                graph_data.append((timestamp, sum(smash_counts)))

            video_serializer = VideoSerializer(videos, many=True)
            serialized_videos = video_serializer.data

            profile_serializer = UserProfileSerializer(profile)
            serialized_profile = profile_serializer.data

            return JsonResponse({'success': True, 
                                 'videos': serialized_videos, 
                                 'profile': serialized_profile,
                                 'graphData': graph_data})
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
    user_profile = _get_user_profile(request.user)
    if not user_profile.isPro() and user_profile.number_of_uploads > settings.FREE_QUOTA:
        print("User has reached free quota, returning")
        return JsonResponse({'trial_done': True})
    else:
        test_url = highpoint.upload_signed_url(request)
        return JsonResponse({'url': test_url})

def dispatch(request):
    payload = {}
    payload["user"] = request.user.username
    body = json.loads(request.body)
    payload["fileName"] = body["fileName"]

    response = create_task(url="/process_task/", payload=payload)
    return JsonResponse({'success': True, 'task': response.name})

import random
@csrf_exempt
def process_task(request):
    current_task_id = request.headers['X-AppEngine-TaskName']#random.randint(1, 100)#
    logging.info("Request received for task {}".format(current_task_id))

    payload = request.body.decode('utf-8')
    #logging.info("Reached process_task!")
    logging.info("Reached task with payload {}".format(payload))
    
    payload_json = json.loads(payload)
    user = payload_json["user"]#request.user#
    fileName = payload_json["fileName"]

    highpoint = HighpointService()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

    length, thumb_url = highpoint.initial_video_data(user, fileName, timestamp)

    user_profile = _get_user_profile(user)
    thumbnail = Image.objects.create(user=user_profile.user, url=thumb_url)
    thumbnail.save()

    task_in_progress = Task.objects.create(task_identifier=current_task_id, is_done=False, progress=0, estimated_time=length, user=user_profile.user, thumbnail=thumbnail)   
    user_profile.tasks_in_progress.add(task_in_progress)
    user_profile.save()
    task_in_progress.save()
    
    highpoint.process(user, fileName, task_in_progress, timestamp)
    return JsonResponse({'success': True})

# Eventually replace with WebSockets
def task_status(request):
    user_profile = _get_user_profile(request.user)
    request_address = _get_user_address(request)
    
    tasks = user_profile.tasks_in_progress.all()
    status = {}

    for task_in_progress in tasks:
        if task_in_progress.thumbnail is not None and not cleanup_task(task_in_progress):
            logging.info("Task in progress {}".format(task_in_progress.task_identifier))

            renewed_url = highpoint.renew_url(task_in_progress.thumbnail.url)
            
            formatted_timestamp = task_in_progress.timestamp.strftime("%I:%M %p, %m/%d/%Y")
            formatted_duration = str(timedelta(seconds=task_in_progress.estimated_time))

            status[task_in_progress.task_identifier] = (
                task_in_progress.progress, 
                renewed_url, 
                formatted_timestamp, 
                formatted_duration,
                request_address,
                task_in_progress.pipeline_stage
            )
        else:
            logging.warn("Task is missing thumbnail image or has been cleaned up.")
    
    user_profile.save()
    print("Status {}".format(status))
    return JsonResponse({'success': True, 'tasks': status})

def fetch_results(request):
    body = json.loads(request.body)
    taskId = body["taskId"]

    logging.info("Fetching results for {}".format(taskId))

    task_result: TaskResult = TaskResult.objects.get(task_identifier=taskId)
    results = highpoint.result_mapper(task_result, request.user)

    print("Results {}".format(results.__dict__))
    return JsonResponse({'success': True, 'results': results.__dict__})

@csrf_exempt
def cleanup(request):
    videos = Video.objects.all()
    print("Running cleanup task with {} videos".format(len(list(videos))))

    for video in videos:
        print("Video timestamp {}".format(video.timestamp))
        time_diff = datetime.now(timezone.utc) - video.timestamp
        hours_elapsed = time_diff.total_seconds()/3600
        print("Hours elapsed {}".format(hours_elapsed))

        if hours_elapsed >= settings.HOURS_LIMIT:
            video_path = video.filesystem_url.name
            print("Deleting video {}".format(video_path))
            video.delete()

            highpoint.cleanup_videos(video_path)
        else:
            print("Video still < {}, keeping.".format(settings.HOURS_LIMIT))
    
    images = Image.objects.all()
    print("Running cleanup task with {} images".format(len(list(images))))

    for image in images:
        print("Image timestamp {}".format(image.timestamp))
        time_diff = datetime.now(timezone.utc) - image.timestamp
        hours_elapsed = time_diff.total_seconds()/3600
        print("Hours elapsed {}".format(hours_elapsed))

        if hours_elapsed >= settings.HOURS_LIMIT:
            print("Deleting image {}".format(image.url))
            image_path = image.url
            image.delete()

            highpoint.cleanup_videos(image_path)
        else:
            print("Image still < {}, keeping.".format(settings.HOURS_LIMIT))

def cleanup_task(task: Task) -> bool:
    logging.info("Task timestamp {}".format(task.timestamp))
    time_diff = datetime.now(timezone.utc) - task.timestamp
    hours_elapsed = time_diff.total_seconds()/3600
    logging.info("Hours elapsed {}".format(hours_elapsed))

    if task.is_done and hours_elapsed >= settings.HOURS_LIMIT:
        task_id = task.task_identifier
        logging.info("Deleting task {}".format(task_id))
        task.delete()

        task_result: TaskResult = TaskResult.objects.get(task_identifier=task_id)
        logging.info("Deleting task result {}".format(task_result.task_identifier))
        task_result.delete()

        return True
    else:
        logging.info("Task still < {}, keeping.".format(settings.HOURS_LIMIT))
        return False

@login_required
def plans(request):
    products = Product.objects.all()
    user_profile = _get_user_profile(request.user)
    context = {
        'products': products,
        'isPro': user_profile.isPro()
    }
    return render(request, 'plans.html', context)

def subscribe(request):
    if request.method == 'POST':
        print("Creating subscription")
        data = json.loads(request.body)
        payment_method = data['payment_method']
        stripe.api_key = settings.STRIPE_TEST_SECRET_KEY

        payment_method_obj = stripe.PaymentMethod.retrieve(payment_method)
        djstripe.models.PaymentMethod.sync_from_stripe_data(payment_method_obj)

        try:
            customer = stripe.Customer.create(
                payment_method=payment_method,
                email=request.user.email,
                invoice_settings={
                    'default_payment_method': payment_method
                },
                name=request.user.username
            )

            djstripe_customer = djstripe.models.Customer.sync_from_stripe_data(customer)
            request.user.customer = djstripe_customer

            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[
                    {
                        "price": data["price_id"]
                    }
                ],
                expand=["latest_invoice.payment_intent"]
            )

            _ = djstripe.models.Subscription.sync_from_stripe_data(subscription)

            user_profile = _get_user_profile(request.user)
            user_profile.subscription = subscription.id
            user_profile.save()

            return JsonResponse(subscription)
        except Exception as e:
            print("Failing with " + str(e))
            return JsonResponse({'error': (e.args[0])}, status=403)
    else:
        return HttpResponse('Request method not allowed')

def cancel_subscription(request):
  if request.user.is_authenticated:
    user_profile = _get_user_profile(request.user)

    stripe.api_key = settings.STRIPE_TEST_SECRET_KEY
    
    try:
      # delete from Stripe
      stripe.Subscription.delete(user_profile.subscription)

      # delete from DB
      Subscription.objects.get(id=user_profile.subscription).delete()

      # update User Profile
      user_profile.subscription = ''
      user_profile.save()

    except Exception as e:
      return JsonResponse({'error test': (e.args[0])}, status = 403)

  # redirect to homepage
  return redirect("homepage")

def signup(request):
    if request.method == 'POST':
        form = RegisterUserForm(request.POST)

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

def warmup(request):
    logging.info("Warmup request received")
    return HttpResponse('Warmup Msg', content_type='text/plain')

# MARK: Private methods

def _get_user_profile(user):
    User = get_user_model()
    user_auth = User.objects.get(username=user) 
    user_p = UserProfile.objects.get(user=user_auth)
    print("Is pro? " + str(user_p.isPro()))
    return user_p

def _get_user_address(request):
    g = GeoIP2()
    remote_addr = request.META.get('HTTP_X_FORWARDED_FOR')
    if remote_addr:
        address = remote_addr.split(',')[-1].strip()
    else:
        address = request.META.get('REMOTE_ADDR')
    try:
        country = g.country_code(address)
        city = g.city(address)['city']

        address = "{}, {}".format(city, country)
        print(address)
        return address
    except:
        print("Failed to find address for {}".format(address))
        return "Unknown Location"
    
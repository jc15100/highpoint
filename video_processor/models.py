from django.db import models
from django.contrib.auth.models import User
from djstripe.models import Subscription

def user_upload_path(instance, filename):
    # Get the username of the user associated with the file
    username = instance.user.username
    # Concatenate the username with the filename to create the upload path
    return f'uploads/{username}/{filename}'

class Image(models.Model):
    user = models.ForeignKey(User,verbose_name='User', related_name="imageUser", on_delete=models.CASCADE)
    url = models.URLField(max_length=1000)
    timestamp = models.DateTimeField(auto_now_add=True, null=True)

class Video(models.Model):
    class VideoTypes(models.TextChoices):
        RAW = 'raw', 'Raw'
        SMASH = 'smash', 'Smash'
        HIGHLIGHT = 'highlight', 'Highlight'

    web_url = models.URLField(max_length=1000)
    user = models.ForeignKey(User,verbose_name='User', related_name="videoUser", on_delete=models.CASCADE)
    filesystem_url = models.FileField()
    timestamp = models.DateTimeField(auto_now_add=True)
    timestamp_string = models.CharField(max_length=100, null=True)
    type = models.CharField(max_length=10, choices=VideoTypes.choices, default=VideoTypes.RAW)

class Task(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True, null=True)
    task_identifier = models.CharField(max_length=100)
    is_done = models.BooleanField(default=False)
    progress = models.FloatField(default=0.0)
    estimated_time = models.FloatField(default=0.0)
    user = models.ForeignKey(User,verbose_name='User', related_name="taskUser", on_delete=models.CASCADE)
    thumbnail = models.OneToOneField(Image, related_name="videoThumbnail", on_delete=models.CASCADE, null=True)

class TaskResult(models.Model):
    task_identifier = models.CharField(max_length=100)
    user = models.ForeignKey(User,verbose_name='User', related_name="taskResultUser", on_delete=models.CASCADE, null=True)

    smashes = models.ManyToManyField(Video, related_name="smashes")
    group_highlight = models.OneToOneField(Video, related_name="groupHighlight", on_delete=models.CASCADE, null=True)
    
    extracted_speeds = models.JSONField(default=dict)
    player_frames = models.ManyToManyField(Image)
    timestamp = models.CharField(max_length=100, null=True)

class UserProfile(models.Model):
    class PlanTypes(models.TextChoices):
        BASIC = 'basic', 'Basic'
        PRO = 'pro', 'Pro'

    user = models.ForeignKey(User,verbose_name='User', related_name="profileUser", on_delete=models.CASCADE)
    plan = models.CharField(max_length=20, choices=PlanTypes.choices, default=PlanTypes.BASIC)
    subscription = models.CharField(max_length=100, default='')
    
    number_of_uploads = models.IntegerField(default=0)
    level = models.FloatField(default=1.0)
    players = models.IntegerField(default=0)

    tasks_in_progress = models.ManyToManyField(Task)

    smashes = models.ManyToManyField(Video)
    highlights = models.ManyToManyField(Video, related_name="highlights_videos")

    def isPro(self):
        try:
            subscription = Subscription.objects.get(id=self.subscription)
            return subscription.status == 'active'
        except Subscription.DoesNotExist:
            return False
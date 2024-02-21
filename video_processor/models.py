from django.db import models
from django.contrib.auth.models import User
from djstripe.models import Subscription

def user_upload_path(instance, filename):
    # Get the username of the user associated with the file
    username = instance.user.username
    # Concatenate the username with the filename to create the upload path
    return f'uploads/{username}/{filename}'

class Video(models.Model):
    class VideoTypes(models.TextChoices):
        RAW = 'raw', 'Raw'
        SMASH = 'smash', 'Smash'
        HIGHLIGHT = 'highlight', 'Highlight'

    web_url = models.URLField(max_length=500)
    user = models.ForeignKey(User,verbose_name='User', related_name="videoUser", on_delete=models.CASCADE)
    filesystem_url = models.FileField()
    timestamp = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=10, choices=VideoTypes.choices, default=VideoTypes.RAW)

class Task(models.Model):
    task_identifier = models.CharField(max_length=100)
    is_done = models.BooleanField(default=False)
    progress = models.FloatField(default=0.0)
    user = models.ForeignKey(User,verbose_name='User', related_name="taskUser", on_delete=models.CASCADE)

class UserProfile(models.Model):
    class PlanTypes(models.TextChoices):
        BASIC = 'basic', 'Basic'
        PRO = 'pro', 'Pro'

    user = models.ForeignKey(User,verbose_name='User', related_name="profileUser", on_delete=models.CASCADE)
    plan = models.CharField(max_length=20, choices=PlanTypes.choices, default=PlanTypes.BASIC)
    
    number_of_uploads = models.IntegerField(default=0)
    level = models.FloatField(default=1.0)
    players = models.IntegerField(default=0)

    tasks_in_progress = models.ManyToManyField(Task)

    smashes = models.ManyToManyField(Video)
    highlights = models.ManyToManyField(Video, related_name="highlights_videos")

    def isPro(self):
        subscription = Subscription.objects.get(id=self.subscription)
        return subscription.status
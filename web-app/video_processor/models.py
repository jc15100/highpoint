from django.db import models
from django.contrib.auth.models import User
from djstripe.models import Subscription

class Video(models.Model):
    class VideoTypes(models.TextChoices):
        RAW = 'raw', 'Raw'
        SMASH = 'smash', 'Smash'
        HIGHLIGHT = 'highlight', 'Highlight'
    
    filesystem_url = models.FileField(upload_to='uploads/%Y/%m/%d')
    web_url = models.URLField()
    user = models.ForeignKey(User,verbose_name='User', related_name="videoUser", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=10, choices=VideoTypes.choices, default=VideoTypes.RAW)

class UserProfile(models.Model):
    class PlanTypes(models.TextChoices):
        BASIC = 'basic', 'Basic'
        PRO = 'pro', 'Pro'

    user = models.ForeignKey(User,verbose_name='User', related_name="profileUser", on_delete=models.CASCADE)
    plan = models.CharField(max_length=20, choices=PlanTypes.choices, default=PlanTypes.BASIC)
    
    number_of_uploads = models.IntegerField()
    level = models.FloatField(default=1.0)
    players = models.IntegerField()

    smashes = models.ManyToManyField(Video)
    highlights = models.ManyToManyField(Video, related_name="highlights_videos")

    def isPro(self):
        subscription = Subscription.objects.get(id=self.subscription)
        return subscription.status
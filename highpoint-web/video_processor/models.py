from django.db import models

class Video(models.Model):
    video_name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    size = models.FloatField()
    duration_secs = models.IntegerField()
    user_id = models.CharField(max_length=100)
    time = models.TimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.video_name



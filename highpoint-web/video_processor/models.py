from django.db import models

class Video(models.Model):
    location = models.FileField(upload_to='uploads/%Y/%m/%d')



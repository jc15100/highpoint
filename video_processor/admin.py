from django.contrib import admin
from .models import *

# register Video
admin.site.register(Video)
admin.site.register(UserProfile)
admin.site.register(Task)
admin.site.register(Image)
admin.site.register(TaskResult)

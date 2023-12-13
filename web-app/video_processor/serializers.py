from rest_framework import routers,serializers,viewsets

from .models import Video

class VideoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Video
        fields = [ 'location' ]
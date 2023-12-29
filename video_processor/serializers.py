from rest_framework import routers,serializers,viewsets

from .models import *

class VideoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Video
        fields = [ 'filesystem_url', 'web_url']

class UserProfileSerializer(serializers.HyperlinkedModelSerializer):
    smashes = VideoSerializer(many=True)
    highlights = VideoSerializer(many=True)

    class Meta:
        model = UserProfile
        fields = [ 'number_of_uploads', 'level', 'players', 'smashes', 'highlights']
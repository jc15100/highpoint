import os
import json
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage, FileSystemStorage
from django.core.files import File
from django.core.files.base import ContentFile
from django.conf import settings

from ml.pipeline.service import RacquetSportsMLService
from ml.pipeline.result import HighpointResult

from ..models import Video, UserProfile
from ml.pipeline.core.storage_helper import StorageHelper

local_storage = FileSystemStorage()
local_storage.base_location = settings.MEDIA_ROOT

class HighpointService:
    def __init__(self):
        self.storage_helper = StorageHelper()
        self.ready = True
        self.mlService = RacquetSportsMLService(self.storage_helper)
    
    def process(self, user, body):
        video_url = self.video_signed_url(user, body)

        # check it's a supported sport video
        supported = self.mlService.check_supported_sport(video_url)

        print("Supported sport? " + str(supported))

        if not supported:
            result = {'supported': False}
        else:
            result = self.mlService.run_processing(video_url, user)
            self.update_db(user, result)

        return result

    def update_db(self, user, result: HighpointResult):
        print("Updating user profile in DB & results in storage for " + str(user))

        if result.supported == True:
            User = get_user_model()
            user_auth = User.objects.get(username=user) 
            user = UserProfile.objects.get(user=user_auth)
            user.number_of_uploads += 1

            # TODO: redo formula for user level considering more than just smashes
            user.level = round(((1 / (len(user.smashes.all()) + 1)) * 0.2) + user.level, 2)
            user.players += 4

            # Update DB
            # (1) smashes
            for smash_name, smash_url in zip(result.smashes, result.smashes_urls):
                smash = Video.objects.create(type=Video.VideoTypes.SMASH, user=user_auth, filesystem_url=smash_name)
                user.smashes.add(smash)

            # (2) highlight
            highlight = Video.objects.create(type=Video.VideoTypes.HIGHLIGHT, user=user_auth, filesystem_url=result.group_highlight)
            user.highlights.add(highlight)

            user.save()
            print("Profile, storage updated for " + str(user))

    def upload_signed_url(self, request):
        body = json.loads(request.body)
        fileName = body['fileName']
        fileType = body['fileType']

        storage_bucket = self.storage_helper.get_storage_bucket_path(request.user, fileName)

        test_url = self.storage_helper.get_signed_url_for_upload(storage_bucket, fileType, "PUT")
        return test_url

    def video_signed_url(self, user, body):
        body = json.loads(body)
        fileName = body['fileName']

        blob_path = self.storage_helper.get_storage_bucket_path(user, fileName)
        video_file = self.storage_helper.get_signed_url(blob_path, "GET")

        return video_file

    def save_video_remotely(self, user, video_path, timestamp):
        # temp_file is to avoid SuspiciousFileOperation while saving from file path
        temp_file = tempfile.NamedTemporaryFile(dir='media')
        video = open(video_path, 'rb')
        temp_file.write(video.read())

        # store in default_storage (GCloud)
        storage_path = "results/" + str(user) + "/" + timestamp + "/" + os.path.basename(video_path)
        
        print("Storing at " + str(storage_path))
        _ = default_storage.save(storage_path, File(temp_file))
        return str(storage_path)
        
    def save_video_locally(self, video):
        # Download file to local filesystem & process it.
        # If the file is not on local storage download it
        print("Saving temp video locally " + str(video.filesystem_url))
        filename = video.filesystem_url.name
        if not local_storage.exists(filename):
            filecontent = video.filesystem_url.read()
            local_storage.save(filename, ContentFile(filecontent))
                
        local_file_path = local_storage.path(filename)
        return local_file_path
    
    def renew_user_content(self, videos: [Video], profile: UserProfile):
        print("Renewing ({}) Raw Videos".format(len(videos)))

        for video in videos:
            url = self.storage_helper.get_signed_url(str(video.filesystem_url), "GET")
            video.web_url = url
        
        print("Renewing ({}) Smash Videos".format(len(profile.smashes.all())))
        for smash in profile.smashes.all():
            smash_url = self.storage_helper.get_signed_url(str(smash.filesystem_url), "GET")
            smash.web_url = smash_url
            print("smash.web_url set to {}".format(smash.web_url))
        
        print("Renewing ({}) Highlight Videos".format(len(profile.highlights.all())))
        for highlight in profile.highlights.all():
            highlight_url = self.storage_helper.get_signed_url(str(highlight.filesystem_url), "GET")
            highlight.web_url = highlight_url
            print("highlight.web_url set to {}".format(highlight.web_url))
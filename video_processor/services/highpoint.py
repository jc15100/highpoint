import os
import json
import tempfile
import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.files.storage import default_storage, FileSystemStorage
from django.core.files import File
from django.core.files.base import ContentFile
from django.conf import settings

from ml.pipeline.service import RacquetSportsMLService
from ml.pipeline.result import HighpointResult

from ..models import Video, UserProfile, TaskResult, Task, Image
from ml.pipeline.core.storage_helper import StorageHelper

local_storage = FileSystemStorage()
local_storage.base_location = settings.MEDIA_ROOT

class HighpointService:
    def __init__(self):
        self.storage_helper = StorageHelper()
        self.ready = True
        self.mlService = RacquetSportsMLService(self.storage_helper)
    
    def estimate_time(self, user, filename):
        video_url = self.file_signed_url(user, filename)
        video_length = self.mlService.video_length(video_url)
        return video_length

    def process(self, user, fileName, task_id):
        video_url = self.file_signed_url(user, fileName)

        # check it's a supported sport video
        supported = self.mlService.check_supported_sport(video_url)
        #supported = True
        logging.info("Supported sport? " + str(supported))

        if not supported:
            result = {'supported': False}
        else:
            result = self.mlService.run_pipeline(video_url, user)
            # result = HighpointResult(
            # smashes=["test"],
            # smashes_urls=["test"],
            # group_highlight="test", 
            # group_highlight_url="test",
            # player_speeds={"test":1}, 
            # player_frames=["test"],
            # player_frames_urls=["test"],
            # supported=True)

            self.update_db(user, result, task_id)

    def update_db(self, user, result: HighpointResult, task_id):
        if result.supported == True:
            User = get_user_model()
            user_auth = User.objects.get(username=user) 

            # Update user profile
            user = UserProfile.objects.get(user=user_auth)
            user.number_of_uploads += 1
            user.level = round(((1 / (len(user.smashes.all()) + 1)) * 0.2) + user.level, 2)
            user.players += 4
            user.save()
            logging.info("Updated user profile {}".format(str(user)))
            
            # Update task in progress & mark it done
            task_in_progress: Task = user.tasks_in_progress.get(task_identifier=task_id)
            task_in_progress.progress = 100
            task_in_progress.is_done = True
            task_in_progress.save()
            logging.info("Updated task in progress with id {}".format(task_id))
            
            # Create a TaskResult and save to DB
            task_result = self.highpoint_mapper(highpoint=result, user=user_auth, task_id=task_id)
            task_result.save()
            logging.info("Created TaskResult with id {}".format(task_id))
        else:
            logging.info("Computed result is not supported!")

    def result_mapper(self, result: TaskResult, user) -> HighpointResult:
        smashes = []
        smash_urls = []

        for smash_video in result.smashes.all():
            smashes.append(smash_video.filesystem_url.name)
            smash_url = self.file_signed_url(user, smash_video.filesystem_url.name)
            smash_urls.append(smash_url)
        
        group_higlight = result.group_highlight.filesystem_url.name
        group_higlight_url = self.file_signed_url(user, group_higlight)

        player_speeds = json.loads(result.extracted_speeds)
        
        player_frames = []
        player_frames_urls = []
        
        for image in result.player_frames.all():
            player_frames.append(image.url)
            player_frames_urls.append(self.file_signed_url(user, image.url))
    
        return HighpointResult(smashes = smashes, 
                               smashes_urls = smash_urls, 
                               group_highlight = group_higlight, 
                               group_highlight_url = group_higlight_url, 
                               player_speeds = player_speeds,
                               player_frames = player_frames, 
                               player_frames_urls = player_frames_urls,
                               supported = True)
    
    def highpoint_mapper(self, highpoint: HighpointResult, user: User, task_id) -> TaskResult:
        task_result = TaskResult.objects.create(task_identifier=task_id)

        highlight = Video.objects.create(type=Video.VideoTypes.HIGHLIGHT, user=user, filesystem_url=highpoint.group_highlight)
        task_result.group_highlight = highlight

        for smash_name in highpoint.smashes:
            smash = Video.objects.create(type=Video.VideoTypes.SMASH, user=user, filesystem_url=smash_name)
            task_result.smashes.add(smash)

        task_result.extracted_speeds = json.dumps(highpoint.player_speeds)

        for player_frame in highpoint.player_frames:
            player_image = Image.objects.create(user=user, url=player_frame)
            task_result.player_frames.add(player_image)

        return task_result

    def upload_signed_url(self, request):
        body = json.loads(request.body)
        fileName = body['fileName']
        fileType = body['fileType']

        storage_bucket = self.storage_helper.get_storage_bucket_path(request.user, fileName)

        test_url = self.storage_helper.get_signed_url_for_upload(storage_bucket, fileType, "PUT")
        return test_url

    def file_signed_url(self, user, fileName):
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
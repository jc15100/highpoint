import os
import json
import tempfile
from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage, FileSystemStorage
from django.core.files import File
from django.core.files.base import ContentFile
from django.conf import settings

from ml.pipeline.service import RacquetSportsMLService
from ml.pipeline.result import HighpointResult

from ..models import Video, UserProfile

local_storage = FileSystemStorage()
local_storage.base_location = settings.MEDIA_ROOT

class Engine:
    def __init__(self):
        self.ready = True
    
    def process(self, video_path, output_path, request):
        service = RacquetSportsMLService()

        # check it's a supported sport video
        supported = service.check_supported_sport(video_path)

        print("Supported sport? " + str(supported))

        if not supported:
            result = {'supported': False}
        else:
            result = service.run_processing(video_path, output_path)

            # For testing
            # result = HighpointResult(smashes=['/Users/juancarlosgarcia/Projects/highpoint/media/smash-433.mp4'],
            #                          group_highlight='/Users/juancarlosgarcia/Projects/highpoint/media/highlight-88.mp4',
            #                          player_speeds={"1": [14.353446312598534, 10.235220283180563, 11.711265002335463], "2": [2565.1064023866757]},
            #                          player_frames=['/Users/juancarlosgarcia/Projects/highpoint/media/frame_0000.png', 
            #                                         '/Users/juancarlosgarcia/Projects/highpoint/media/frame_0001.png', 
            #                                         '/Users/juancarlosgarcia/Projects/highpoint/media/frame_0002.png', 
            #                                         '/Users/juancarlosgarcia/Projects/highpoint/media/frame_0003.png'],
            #                         supported=True)

            result = self.store_results(request, result)
            print(json.dumps(result.__dict__))

        return result

    def store_results(self, request, result):
        print("Updating user profile in DB & results in storage for " + str(request.user))

        smashes_urls = []
        player_frames_urls = []
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        if result.supported == True:
            User = get_user_model()
            user_auth = User.objects.get(username=request.user) 
            user = UserProfile.objects.get(user=user_auth)
            user.number_of_uploads += 1

            # TODO: redo formula for user level considering more than just smashes
            user.level = round(((1 / (len(user.smashes.all()) + 1)) * 0.2) + user.level, 2)
            user.players += 4

            # Store media results in Google cloud: smashes, group highlight and player frames
            # (1) smashes
            for smash_file in result.smashes:
                smash_url = self.save_video_remotely(request.user, smash_file, timestamp)
                smashes_urls.append(smash_url)
                smash = Video.objects.create(type=Video.VideoTypes.SMASH, user=user_auth, web_url=smash_url)
                user.smashes.add(smash)
            
            # (2) player frames
            for frame_file in result.player_frames:
                frame_url = self.save_video_remotely(request.user, frame_file, timestamp)
                player_frames_urls.append(frame_url)

            # (3) highlight
            highlight_file = result.group_highlight
            highlight_url = self.save_video_remotely(request.user, highlight_file, timestamp)
            highlight = Video.objects.create(type=Video.VideoTypes.HIGHLIGHT, user=user_auth, web_url=highlight_url)
            user.highlights.add(highlight)

            user.save()
            print("Profile, storage updated for " + str(request.user))

            # return a new HighpointResult with urls pointing to Google Storage
            return HighpointResult(
                smashes=smashes_urls, 
                group_highlight=highlight_url, 
                player_speeds=result.player_speeds, 
                player_frames=player_frames_urls, 
                supported=True
            )
    
    def save_video_remotely(self, user, video_path, timestamp):
        # temp_file is to avoid SuspiciousFileOperation while saving from file path
        temp_file = tempfile.NamedTemporaryFile(dir='media')
        video = open(video_path, 'rb')
        temp_file.write(video.read())

        # store in default_storage (GCloud)
        storage_path = "results/" + str(user) + "/" + timestamp + "/" + os.path.basename(video_path)
        
        print("Storing at " + str(storage_path))
        path = default_storage.save(storage_path, File(temp_file))
        #return default_storage.url(path)
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
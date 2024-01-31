from google.cloud import storage
from google.cloud.storage._signing import generate_signed_url_v4
from django.conf import settings
import datetime
import io
import cv2

class StorageHelper:
    def get_storage_client(self):
        return storage.Client.from_service_account_json(settings.CREDENTIALS_JSON)

    def get_canonical_path(self, sub_bucket):
        return "/" + settings.GS_BUCKET_NAME + "/" + sub_bucket

    def get_storage_bucket_path(self, user, filename):
        return "media" + "/{}/".format(user) + filename

    def get_results_bucket_path(self, user, filename, timestamp):
        return "results" + "/{}/{}/".format(user, timestamp) + filename

    def download_local_copy(self, user, blob_path):
        client = self.get_storage_client()
        bucket_name = settings.GS_BUCKET_NAME
        bucket = client.get_bucket(bucket_name)
        video_blob = bucket.blob(blob_path)

        local_video_path = str(settings.MEDIA_ROOT) + "/{}_local_video.mp4".format(str(user))
        video_blob.download_to_filename(local_video_path)
        return local_video_path

    def open_file(self, user, blob_path):
        client = self.get_storage_client()
        bucket_name = settings.GS_BUCKET_NAME
        bucket = client.get_bucket(bucket_name)
        video_blob = bucket.blob(blob_path)
        return video_blob.open('rb')
    
    def get_blob(self, bucket_path):
        client = self.get_storage_client()
        bucket_name = settings.GS_BUCKET_NAME
        bucket = client.get_bucket(bucket_name)
        video_blob = bucket.blob(bucket_path)
        return video_blob

    def get_signed_url_for_upload(self, sub_bucket, content_type, method):
        client = self.get_storage_client()
        expiration = datetime.timedelta(minutes=15)
        canonical_resource = self.get_canonical_path(sub_bucket)

        url = generate_signed_url_v4(
            client._credentials,
            resource=canonical_resource,
            api_access_endpoint=settings.API_ACCESS_ENDPOINT,
            expiration=expiration,
            method=method,
            content_type=content_type
        )

        print("Generated signed url for upload: " + str(url))
        return url

    def get_signed_url(self, sub_bucket, method):
        client = self.get_storage_client()
        expiration = datetime.timedelta(minutes=15)
        canonical_resource = self.get_canonical_path(sub_bucket)

        url = generate_signed_url_v4(
            client._credentials,
            resource=canonical_resource,
            api_access_endpoint=settings.API_ACCESS_ENDPOINT,
            expiration=expiration,
            method=method
        )

        print("Generated signed url for viewing: " + str(url))
        return url
    
    def upload_frame(self, frame, blob):
        _, image_buffer = cv2.imencode(".png", frame)
        image_bytes_io = io.BytesIO()
        image_bytes_io.write(image_buffer)

        image_bytes_io.seek(0)
        blob.upload_from_file(image_bytes_io, content_type='image/png')
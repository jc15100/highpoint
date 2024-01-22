from google.cloud import storage
from google.cloud.storage._signing import generate_signed_url_v4
from django.conf import settings
import datetime

class StorageHelper:
    def get_storage_client(self):
        return storage.Client.from_service_account_json(settings.CREDENTIALS_JSON)

    def get_canonical_path(self, sub_bucket):
        return "/" + settings.GS_BUCKET_NAME + "/" + sub_bucket

    def get_storage_bucket_path(self, user, filename):
        return "media" + "/{}/".format(user) + filename

    def get_results_bucket_path(self, user, filename):
        return "results" + "/{}/".format(user) + filename

    def get_local_copy(self, user, blob_path):
        client = self.get_storage_client()
        bucket_name = settings.GS_BUCKET_NAME
        bucket = client.get_bucket(bucket_name)
        video_blob = bucket.blob(blob_path)

        local_video_path = str(settings.MEDIA_ROOT) + "/{}_local_video.mp4".format(str(user))
        video_blob.download_to_filename(local_video_path)
        return local_video_path

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

        print("generated signed url " + str(url))
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

        print("generated signed url " + str(url))
        return url
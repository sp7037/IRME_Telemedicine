"""Private object storage; download URLs always pass through the application ACL."""
from urllib.parse import quote
from django.conf import settings
from storages.backends.s3 import S3Storage


class PrivateS3Storage(S3Storage):
    def url(self, name, parameters=None, expire=None, http_method=None):
        # Never expose bucket URLs or bypass the per-record authorisation view.
        return settings.MEDIA_URL + quote(name.lstrip("/"), safe="/")

# Owner: Nazim Ali Firdous
from django.conf import settings
from django.core.files.storage import FileSystemStorage


def get_private_storage():
    # A function (not an object) so migrations don't hard-code your local path
    return FileSystemStorage(location=settings.PRIVATE_MEDIA_ROOT)
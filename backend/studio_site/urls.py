from django.urls import path

from studio.api import api
from studio.log_stream import stream_logs

urlpatterns = [
    path("api/logs/stream", stream_logs),
    path("api/", api.urls),
]

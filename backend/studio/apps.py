from django.apps import AppConfig


class StudioConfig(AppConfig):
    name = "studio"

    def ready(self) -> None:
        """The API logs as "api"; the worker command switches its own process to "worker"."""
        from studio.logs import configure_logging

        configure_logging("api")

from django.apps import AppConfig


class GroupsConfig(AppConfig):
    name = 'groups'

    def ready(self):
        from . import signals  # noqa: F401  (register signal handlers)

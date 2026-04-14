from django.apps import AppConfig

class SpeakprojectConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'speakproject'

    def ready(self):
        from .scheduler import start_scheduler
        start_scheduler()
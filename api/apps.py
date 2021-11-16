from django.apps import AppConfig
from .models import NSFWModel


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        NSFWModel._load_model()

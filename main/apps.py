from django.apps import AppConfig


class MainConfig(AppConfig):
    name = 'main'
    verbose_name = 'Main'


    def ready(self):
        import main.signals.handlers

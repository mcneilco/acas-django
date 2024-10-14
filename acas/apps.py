from django.apps import AppConfig


class ACASConfig(AppConfig):
    name = "acas"

    def ready(self):
        import acas.signals

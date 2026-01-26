from django.apps import AppConfig


class InvestmentConfig(AppConfig):
    name = 'investment'


    def ready(self):
        import investment.signals
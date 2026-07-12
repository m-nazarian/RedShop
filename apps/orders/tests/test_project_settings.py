from django.test import TestCase


class ProjectSettingsTests(TestCase):
    def test_logging_configuration_is_available(self):
        from django.conf import settings

        self.assertIn("version", settings.LOGGING)
        self.assertEqual(settings.LOGGING["version"], 1)
        self.assertIn("handlers", settings.LOGGING)
        self.assertIn("loggers", settings.LOGGING)
        self.assertIn("apps", settings.LOGGING["loggers"])
        self.assertIn("django.request", settings.LOGGING["loggers"])

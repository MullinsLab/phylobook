import logging
log = logging.getLogger("test")

from django.test import TestCase, TransactionTestCase, SimpleTestCase
from django.contrib.auth.models import User

class TemplateAndViewTests(SimpleTestCase):
    """ Test that templates and views are working """

    databases = "__all__"

    @classmethod
    def setUpTestData(cls):
        """ Set up whatever objects are going to be needed for all tests """

        cls.user = User.objects.create(username="testuser")
        cls.user.set_password("12345")
        cls.user.save()
    
    def setUp(self):
        """ Log in the user """

        try:
            self.user = User.objects.get(username="testuser")
        except User.DoesNotExist:
            self.user = User.objects.create(username="testuser")
            self.user.set_password("12345")
            self.user.save()

        self.client.login(username=self.user.username, password="12345")

    def test_homepage_should_redirect_to_projects(self):
        """ The homepage should redirect to the projects page """

        response = self.client.get("/")
        log.debug(response)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/projects")

    def test_projects_should_load(self):
        """ The projects page should load """

        response = self.client.get("/projects/")
        log.debug(response)

        self.assertEqual(response.status_code, 200)
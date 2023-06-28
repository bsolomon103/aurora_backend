from django.test import TestCase
from .models import Models
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
import torch



class SessionVariableTestCase(TestCase):
    def test_count_is_number(self):
        session = self.client.session
        session["count"] = 10
        session.save()
        self.assertIsInstance(session["count"], (int, float), "Count is not a number")
        session["count"] = "invalid"
        session.save()
        self.assertNotIsInstance(session["count"], (int, float), "Count is not a number")

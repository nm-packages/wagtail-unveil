"""
Base test classes for wagtail-unveil tests.

This module provides common functionality and setup for all test cases
to reduce code duplication across test files.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase


class BaseWagtailUnveilTestCase(TestCase):
    """Base test case with common user creation functionality for all wagtail-unveil tests."""

    def create_test_users(self):
        """Create common test users (superuser and regular user)."""
        User = get_user_model()
        self.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="password123"
        )
        self.regular_user = User.objects.create_user(
            username="user", email="user@example.com", password="password123"
        )

    def create_superuser(
        self, username="admin", email="admin@example.com", password="password123"
    ):
        """Create a superuser with default or custom credentials."""
        User = get_user_model()
        return User.objects.create_superuser(
            username=username, email=email, password=password
        )

    def create_regular_user(
        self, username="user", email="user@example.com", password="password123"
    ):
        """Create a regular user with default or custom credentials."""
        User = get_user_model()
        return User.objects.create_user(
            username=username, email=email, password=password
        )

    def login_as_superuser(self, user=None):
        """Login as superuser. If user is not provided, creates and uses the default superuser."""
        if user is None:
            if not hasattr(self, "superuser"):
                self.superuser = self.create_superuser()
            user = self.superuser
        self.client.login(username=user.username, password="password123")
        return user

    def login_as_regular_user(self, user=None):
        """Login as regular user. If user is not provided, creates and uses the default regular user."""
        if user is None:
            if not hasattr(self, "regular_user"):
                self.regular_user = self.create_regular_user()
            user = self.regular_user
        self.client.login(username=user.username, password="password123")
        return user

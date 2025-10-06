"""
Pytest configuration for paygate project.
"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def pytest_configure():
    """Configure pytest for Django."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paygate_project.test_settings')
    django.setup()

def pytest_unconfigure():
    """Clean up after tests."""
    pass
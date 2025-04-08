import pytest
import os
import sys
import django
from django.conf import settings

# Django 설정 로드
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'graduateCheck.settings')
django.setup()

# 테스트 설정
def pytest_configure():
    settings.DEBUG = False 
"""
URL configuration for graduateCheck project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from myapp.views import upload_file, cleanup_files, analyze

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', upload_file, name='index'),
    path('upload/', upload_file, name='upload'),
    path('analyze/', analyze, name='analyze'),
    path('cleanup/', cleanup_files, name='cleanup'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

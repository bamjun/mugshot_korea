from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from a_users.views import profile_view, service_about_view
from a_home.views import *
from a_board.views import post_list
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', post_list, name='home'),
    path('profile/', include('a_users.urls')),
    path('accounts/', include('allauth.urls')),
    path('@<username>/', profile_view, name='profile'),
    path('board/', include('a_board.urls')),
    path('about/', service_about_view, name='service-about'),
]

# Only used in development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

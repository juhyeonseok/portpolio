"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import (
    HomeView, 
    AdminDashboardView, 
    AdminUserToggleActiveView, 
    AdminPostTogglePublishView, 
    AdminSeriesDeleteView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', HomeView.as_view(), name='home'),
    
    # Custom Apps
    path('accounts/', include('accounts.urls')),
    path('blog/', include('blog.urls')),
    path('portfolio/', include('portfolio.urls')),
    
    # Admin Panel Custom Console
    path('admin-panel/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin-panel/user/<int:pk>/toggle/', AdminUserToggleActiveView.as_view(), name='admin_user_toggle'),
    path('admin-panel/post/<int:pk>/toggle/', AdminPostTogglePublishView.as_view(), name='admin_post_toggle'),
    path('admin-panel/series/<int:pk>/delete/', AdminSeriesDeleteView.as_view(), name='admin_series_delete'),
]

# Serve static/media files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Premium Error Custom Handlers
handler403 = 'core.views.error_403_view'
handler404 = 'core.views.error_404_view'
handler500 = 'core.views.error_500_view'

from django.urls import path
from . import views

app_name = 'portfolio'

urlpatterns = [
    path('', views.PortfolioView.as_view(), name='index'),
    path('edit/', views.PortfolioEditView.as_view(), name='edit'),
    path('update-profile/', views.UpdateProfileInfoView.as_view(), name='update_profile'),
    path('upload-image/', views.UploadProfileImageView.as_view(), name='upload_image'),
    path('add-item/', views.AddPortfolioItemView.as_view(), name='add_item'),
    path('delete-item/<int:pk>/', views.DeletePortfolioItemView.as_view(), name='delete_item'),
]

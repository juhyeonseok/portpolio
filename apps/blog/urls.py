from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.PostListView.as_view(), name='index'),
    path('write/', views.PostCreateView.as_view(), name='create'),
    path('upload-image/', views.UploadBlogImageView.as_view(), name='upload_image'),
    
    # Post Interactions
    path('<int:pk>/like/', views.TogglePostLikeView.as_view(), name='like_post'),
    path('<int:pk>/comment/add/', views.CommentCreateView.as_view(), name='add_comment'),
    path('comment/<int:pk>/delete/', views.CommentDeleteView.as_view(), name='delete_comment'),
    path('comment/<int:pk>/react/<str:reaction_type>/', views.ToggleCommentReactionView.as_view(), name='comment_react'),
    
    # Post Detail and Edit
    path('<str:slug>/', views.PostDetailView.as_view(), name='detail'),
    path('<str:slug>/edit/', views.PostUpdateView.as_view(), name='update'),
]

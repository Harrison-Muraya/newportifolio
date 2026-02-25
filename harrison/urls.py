from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('upload-image/', views.upload_image, name='upload_image'),
    path('toggle-like/<int:image_id>/', views.toggle_like, name='toggle_like'),
    path('add-comment/<int:image_id>/', views.add_comment, name='add_comment'),
    path('image-data/<int:image_id>/', views.get_image_data, name='image_data'),
    path('send-message/', views.send_message, name='send_message'),
]
from django.urls import path
from . import views

urlpatterns = [
    # ── Public ──────────────────────────────────────
    path('', views.home, name='home'),
    path('work/', views.work, name='work'),
    path('work/<slug:slug>/', views.work_detail, name='work_detail'),
    path('lab/', views.lab, name='lab'),
    path('about/', views.about, name='about'),
    path('chat/', views.agent_chat, name='agent_chat'),
    path('chat/send/', views.agent_chat_send, name='agent_chat_send'),
    path('chat/stream/', views.agent_chat_stream, name='agent_chat_stream'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # ── Gallery API ──────────────────────────────────
    path('upload-image/', views.upload_image, name='upload_image'),
    path('toggle-like/<int:image_id>/', views.toggle_like, name='toggle_like'),
    path('add-comment/<int:image_id>/', views.add_comment, name='add_comment'),
    path('image-data/<int:image_id>/', views.get_image_data, name='image_data'),
    path('send-message/', views.send_message, name='send_message'),
    path('project-bg/<int:project_id>/', views.upload_project_bg, name='upload_project_bg'),

    # ── Superuser Dashboard ──────────────────────────
    path('dashboard/', views.dashboard, name='dashboard'),

    # Messages inbox
    path('dashboard/inbox/', views.inbox, name='inbox'),
    path('dashboard/inbox/<int:message_id>/', views.message_detail, name='message_detail'),
    path('dashboard/inbox/<int:message_id>/toggle-read/', views.message_toggle_read, name='message_toggle_read'),
    path('dashboard/inbox/<int:message_id>/delete/', views.message_delete, name='message_delete'),

    # Agent training inbox (superuser)
    path('dashboard/training/', views.training_inbox, name='training_inbox'),
    path('dashboard/training/reward/', views.training_reward, name='training_reward'),

    # Projects CRUD
    path('dashboard/projects/', views.project_list, name='project_list'),
    path('dashboard/projects/create/', views.project_create, name='project_create'),
    path('dashboard/projects/<int:project_id>/edit/', views.project_edit, name='project_edit'),
    path('dashboard/projects/<int:project_id>/delete/', views.project_delete, name='project_delete'),
]
# detection/urls.py
from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    # ==================== APIs para frontend (EXISTENTES) ====================
    path('api/cameras/', api_views.camera_list, name='api_cameras'),
    path('api/detections/<int:camera_id>/', api_views.detection_history, name='api_detections'),
    path('api/stats/', api_views.occupancy_stats, name='api_stats'),
    
    # ==================== Vistas HTML (EXISTENTES) ====================
    path('web/login/', views.login_page, name='login_page'),
    path('web/login/submit/', views.login_submit, name='login_submit'),
    path('web/logout/', views.logout_view, name='logout_view'),
    path('web/dashboard/', views.dashboard, name='dashboard'),
    path('web/cameras/add/', views.add_camera_web, name='add_camera_web'),
    path('web/cameras/<str:camera_sanitized_name>/control/', views.control_camera_web, name='control_camera_web'),
    path('web/cameras/<str:camera_sanitized_name>/remove/', views.remove_camera_web, name='remove_camera_web'),
    path('web/cameras/control-all/', views.control_all_web, name='control_all_web'),
    
    # ==================== STREAMS DE VIDEO ====================
    # Stream CON bounding boxes (YOLO)
    path('stream/<str:camera_sanitized_name>/', views.video_feed, name='video-feed'),
    # Stream SIN bounding boxes (original)
    path('stream/<str:camera_sanitized_name>/original/', views.video_feed_original, name='video-feed-original'),
    
    # ==================== APIs públicas ====================
    path('health/', views.health_check, name='health-check'),
    
    # ==================== APIs para YOLO y bounding boxes ====================
    
    # APIs para listar y gestionar cámaras
    path('api/cameras/all/', views.all_cameras_api, name='all_cameras_api'),
    path('api/cameras/add/', views.add_camera_api, name='add_camera_api'),
    path('api/cameras/<str:camera_id>/start/', views.start_camera_api, name='start_camera_api'),
    path('api/cameras/<str:camera_id>/stop/', views.stop_camera_api, name='stop_camera_api'),
    path('api/cameras/<str:camera_id>/remove/', views.remove_camera_api, name='remove_camera_api'),
    
    # APIs para obtener frames estáticos (una sola imagen)
    path('api/cameras/<str:camera_id>/frame/', views.camera_frame_api, name='camera_frame_api'),
    # URL separada para frame con bounding boxes
    path('api/cameras/<str:camera_id>/frame-with-boxes/', 
         views.camera_frame_with_boxes_api, name='camera_frame_with_boxes_api'),
    
    # APIs para detecciones YOLO
    path('api/cameras/<str:camera_id>/detections/', 
         views.camera_detections_api, name='camera_detections_api'),
    path('api/cameras/<str:camera_id>/status/', 
         views.camera_status_api, name='camera_status_api'),
    
    # Vista especial para pruebas YOLO
    path('web/yolo-test/<str:camera_sanitized_name>/', 
         views.yolo_test_view, name='yolo_test_view'),
    
    # ==================== Root - redirige al login ====================
    path('', views.login_page, name='api-root'),
]
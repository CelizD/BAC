# dashboard/views.py - VERSIÓN SIN EMULACIÓN
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import json

from detection.camera_manager import camera_manager

@csrf_exempt
def camera_detections_view(request, camera_id):
    """
    Obtener lista de detecciones REALES de una cámara
    ⚠️ SIN DATOS SIMULADOS
    """
    try:
        # Obtener detecciones REALES del CameraManager
        detections = camera_manager.get_camera_detections(camera_id, limit=20)
        
        # Obtener estadísticas REALES
        stats = camera_manager.get_detection_statistics(camera_id)
        
        return JsonResponse({
            'camera_id': camera_id,
            'detections': detections,  # ← SOLO detecciones reales de YOLO
            'count': len(detections),
            'statistics': stats,
            'yolo_enabled': stats.get('yolo_enabled', False),
            'message': 'Detecciones REALES' if stats.get('yolo_enabled') else 'YOLO no disponible - instalar ultralytics'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def add_camera_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            camera_id = data.get('camera_id')
            youtube_url = data.get('youtube_url')
            
            success = camera_manager.add_camera(camera_id, youtube_url)
            
            if success:
                return JsonResponse({
                    'success': True,
                    'message': 'Cámara agregada exitosamente'
                })
            else:
                return JsonResponse({
                    'error': 'No se pudo agregar la cámara'
                }, status=400)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt 
def start_camera_view(request, camera_id):
    if request.method == 'POST':
        success = camera_manager.start_camera(camera_id)
        return JsonResponse({'success': success})
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
def stop_camera_view(request, camera_id):
    if request.method == 'POST':
        camera_manager.stop_camera(camera_id)
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
def camera_status_view(request, camera_id):
    status = camera_manager.get_camera_status(camera_id)
    if status:
        return JsonResponse(status)
    return JsonResponse({'error': 'Cámara no encontrada'}, status=404)

def camera_frame_view(request, camera_id):
    """Retorna frame REAL de la cámara (con o sin bounding boxes)"""
    with_boxes = request.GET.get('boxes', 'true').lower() == 'true'
    
    frame_data = camera_manager.get_camera_frame(camera_id, with_boxes=with_boxes)
    
    if frame_data:
        return HttpResponse(frame_data, content_type='image/jpeg')
    
    # Si no hay frame, retornar error (NO imagen placeholder)
    return HttpResponse(status=404)

@csrf_exempt
def remove_camera_view(request, camera_id):
    if request.method == 'POST':
        camera_manager.remove_camera(camera_id)
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Método no permitido'}, status=405)

def all_cameras_view(request):
    """Lista de todas las cámaras con información REAL"""
    cameras = camera_manager.get_cameras_info()
    return JsonResponse({
        'cameras': cameras,
        'total': len(cameras)
    })

def dashboard_view(request):
    return render(request, 'dashboard/index.html')
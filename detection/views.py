# detection/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .yolo_detector import detector

@csrf_exempt
def add_camera(request):
    """Agregar cámara ESP32"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            url = data.get('url')
            
            if not name or not url:
                return JsonResponse({'error': 'Nombre y URL son requeridos'}, status=400)
            
            detector.add_camera(name, url)
            return JsonResponse({
                'status': 'added', 
                'camera': name,
                'message': f'Cámara {name} agregada correctamente'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
def start_detection(request):
    """Iniciar detección"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            camera_name = data.get('camera_name')
            
            if camera_name == 'all':
                started_count = detector.start_all()
                return JsonResponse({
                    'status': 'all_started',
                    'started_count': started_count,
                    'total_cameras': len(detector.cameras)
                })
            else:
                success = detector.start_detection(camera_name)
                if success:
                    return JsonResponse({
                        'status': 'started', 
                        'camera': camera_name,
                        'message': f'Detección iniciada para {camera_name}'
                    })
                else:
                    return JsonResponse({'error': f'Cámara {camera_name} no encontrada'}, status=404)
                    
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
def stop_detection(request):
    """Detener detección"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            camera_name = data.get('camera_name')
            
            if camera_name == 'all':
                detector.stop_all()
                return JsonResponse({'status': 'all_stopped'})
            else:
                detector.stop_detection(camera_name)
                return JsonResponse({
                    'status': 'stopped', 
                    'camera': camera_name
                })
                    
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
def remove_camera(request):
    """Remover cámara"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            camera_name = data.get('camera_name')
            
            success = detector.remove_camera(camera_name)
            if success:
                return JsonResponse({
                    'status': 'removed', 
                    'camera': camera_name
                })
            else:
                return JsonResponse({'error': f'Cámara {camera_name} no encontrada'}, status=404)
                    
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

def get_attendance(request):
    """Obtener datos de asistencia"""
    camera_name = request.GET.get('camera', 'all')
    
    try:
        if camera_name == 'all':
            cameras_data = detector.get_all_cameras_data()
            data = {}
            for name, camera_data in cameras_data.items():
                data[name] = {
                    'person_count': camera_data['person_count'],
                    'chair_count': camera_data['chair_count'],
                    'occupancy_rate': camera_data['occupancy_rate'],
                    'status': camera_data['status'],
                    'fps': camera_data['fps'],
                    'last_update': camera_data['last_update'].isoformat()
                }
            return JsonResponse(data)
        else:
            camera_data = detector.get_camera_data(camera_name)
            if camera_data:
                return JsonResponse({
                    'person_count': camera_data['person_count'],
                    'chair_count': camera_data['chair_count'],
                    'occupancy_rate': camera_data['occupancy_rate'],
                    'status': camera_data['status'],
                    'fps': camera_data['fps'],
                    'last_update': camera_data['last_update'].isoformat()
                })
            return JsonResponse({'error': 'Cámara no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
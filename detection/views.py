from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import json
import cv2
import re
import time
import numpy as np
from datetime import datetime
from urllib.parse import urlparse

# Camera manager
from .camera_manager import camera_manager

<<<<<<< HEAD
# ============================================================
# Helpers
# ============================================================
=======
def camera_frame_with_boxes_api(request, camera_id):
    """API específica para frame CON bounding boxes"""
    # Llamar a camera_frame_api con boxes=True
    return camera_frame_api(request, camera_id, boxes=True)
>>>>>>> 94a56a6 (yolo activo!)

def sanitize_camera_name(name):
    if not name or not name.strip():
        return "camara_sin_nombre"
    name = re.sub(r'[^\w\s-]', '', name.strip())
    name = re.sub(r'[-\s]+', '_', name)
    return name.lower() or "camara_sin_nombre"

def normalize_stream_url(url):
    if not url:
        return url
    url = url.strip()
    if url.startswith(('http://', 'https://', 'rtsp://')):
        return url
    return 'http://' + url

# ============================================================
# Auth Views
# ============================================================

def login_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'detection/login.html')

@csrf_exempt
def login_submit(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            auth_login(request, user)
            request.session['user_cameras'] = []
            return redirect('dashboard')
        return render(request, 'detection/login.html', {'error': 'Credenciales incorrectas'})
    return redirect('login_page')

def logout_view(request):
    if 'user_cameras' in request.session:
        for cam in request.session['user_cameras']:
            name = cam.get('sanitized_name')
            if name:
                try:
                    camera_manager.stop_camera(name)
                    camera_manager.remove_camera(name)
                except: pass

    auth_logout(request)
    messages.success(request, 'Sesión cerrada')
    return redirect('login_page')

# ============================================================
# Dashboard
# ============================================================

@login_required
def dashboard(request):
    if 'user_cameras' not in request.session:
        request.session['user_cameras'] = []

    cameras_info = []
    for cam_data in request.session['user_cameras']:
        try:
            name = cam_data.get('sanitized_name')
            if not name:
                continue

            status = camera_manager.get_camera_status(name)
            if not status:
                continue

            detections = camera_manager.get_camera_detections(name, limit=10)
            stats = camera_manager.get_detection_statistics(name)

            status.update({
                'original_name': cam_data['original_name'],
                'sanitized_name': name,
                'stream_url': cam_data['stream_url'],
                'clean_url': cam_data['stream_url'].replace('http://',''),
                'recent_detections': detections,
                'detection_count': len(detections),
                'detection_stats': stats
            })
            cameras_info.append(status)
        except Exception as e:
            print("Error:", e)
            continue

    return render(request, 'detection/dashboard.html', {'cameras': cameras_info})

# ============================================================
# Web Controls (HTML)
# ============================================================

@login_required
@csrf_exempt
def add_camera_view(request):
    if request.method == 'POST':
        original = request.POST.get('camera_name')
        url = request.POST.get('stream_url')

        if not original or not url:
            messages.error(request, 'Nombre y URL son requeridos')
            return redirect('dashboard')

        sanitized = sanitize_camera_name(original)
        final_url = normalize_stream_url(url)

        # evitar duplicados
        if any(c['sanitized_name'] == sanitized for c in request.session['user_cameras']):
            messages.error(request, 'Cámara ya existente')
            return redirect('dashboard')

        camera_manager.add_camera(sanitized, final_url)

        request.session['user_cameras'].append({
            'original_name': original,
            'sanitized_name': sanitized,
            'stream_url': final_url
        })
        request.session.modified = True

        messages.success(request, 'Cámara agregada')
    return redirect('dashboard')

@login_required
@csrf_exempt
def remove_camera_view(request, camera_id):
    if request.method == 'POST':
        try:
            camera_manager.stop_camera(camera_id)
            camera_manager.remove_camera(camera_id)
        except: pass

        request.session['user_cameras'] = [
            c for c in request.session['user_cameras']
            if c['sanitized_name'] != camera_id
        ]
        request.session.modified = True

        messages.success(request, 'Cámara eliminada')
    return redirect('dashboard')

@login_required
@csrf_exempt
def start_camera_view(request, camera_id):
    """ ← ESTA ERA LA FUNCIÓN FALTANTE """
    try:
        camera_manager.start_camera(camera_id)
        return JsonResponse({'success': True, 'message': f'Cámara {camera_id} iniciada'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@csrf_exempt
def stop_camera_view(request, camera_id):
    try:
        camera_manager.stop_camera(camera_id)
        return JsonResponse({'success': True, 'message': f'Cámara {camera_id} detenida'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def camera_status_view(request, camera_id):
    status = camera_manager.get_camera_status(camera_id)
    if not status:
        return JsonResponse({'error': 'No encontrada'}, status=404)
    return JsonResponse(status)

@login_required
def camera_frame_view(request, camera_id):
    frame = camera_manager.get_camera_frame(camera_id, with_boxes=True)
    if frame:
        return HttpResponse(frame, content_type='image/jpeg')
    return HttpResponse(status=404)

@login_required
def camera_detections_view(request, camera_id):
    detections = camera_manager.get_camera_detections(camera_id, limit=20)
    return JsonResponse({'camera_id': camera_id, 'detections': detections})

@login_required
def all_cameras_view(request):
    info = camera_manager.get_cameras_info()
    return JsonResponse({'cameras': info})

# ============================================================
# Streaming
# ============================================================

def video_feed(request, camera_id):
    def generate():
        while True:
            data = camera_manager.get_camera_status(camera_id)
            if data and data.get('last_frame') is not None:
                ok, buffer = cv2.imencode('.jpg', data['last_frame'], [cv2.IMWRITE_JPEG_QUALITY, 70])
                if ok:
                    yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' +
                           buffer.tobytes() + b'\r\n')
            time.sleep(0.1)

    return StreamingHttpResponse(generate(),
        content_type='multipart/x-mixed-replace; boundary=frame')

# ============================================================
# YOLO Test Page
# ============================================================

@login_required
def yolo_test_view(request, camera_id):
    status = camera_manager.get_camera_status(camera_id)
    if not status:
        messages.error(request, 'Cámara no encontrada')
        return redirect('dashboard')

    detections = camera_manager.get_camera_detections(camera_id, limit=20)
    stats = camera_manager.get_detection_statistics(camera_id)

    return render(request, 'detection/yolo_test.html', {
        'camera': status,
        'recent_detections': detections,
        'detection_stats': stats,
        'camera_name': camera_id
    })
# ============================================================
# Web Controls (FUNCIONES FALTANTES)
# ============================================================

@login_required
@csrf_exempt
def add_camera_web(request):
    """Agregar cámara desde el dashboard web"""
    if request.method == 'POST':
        camera_name = request.POST.get('camera_name', '').strip()
        stream_url = request.POST.get('stream_url', '').strip()
        camera_user = request.POST.get('camera_user', 'admin')
        camera_password = request.POST.get('camera_password', 'admin123')
        
        if not camera_name or not stream_url:
            messages.error(request, 'Nombre y URL son requeridos')
            return redirect('dashboard')
        
        sanitized = sanitize_camera_name(camera_name)
        final_url = normalize_stream_url(stream_url)
        
        # Evitar duplicados
        if 'user_cameras' not in request.session:
            request.session['user_cameras'] = []
        
        if any(c['sanitized_name'] == sanitized for c in request.session['user_cameras']):
            messages.error(request, f'La cámara "{camera_name}" ya existe')
            return redirect('dashboard')
        
        # Agregar cámara al manager
        camera_manager.add_camera(sanitized, final_url)
        
        # Guardar en sesión
        request.session['user_cameras'].append({
            'original_name': camera_name,
            'sanitized_name': sanitized,
            'stream_url': final_url,
            'username': camera_user,
            'password': camera_password
        })
        request.session.modified = True
        
        messages.success(request, f'Cámara "{camera_name}" agregada correctamente')
        return redirect('dashboard')
    
    return redirect('dashboard')

@login_required
@csrf_exempt
def control_camera_web(request, camera_sanitized_name):
    """Controlar una cámara específica (iniciar/detener)"""
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'start':
            try:
                camera_manager.start_camera(camera_sanitized_name)
                messages.success(request, f'Cámara "{camera_sanitized_name}" iniciada')
            except Exception as e:
                messages.error(request, f'Error al iniciar cámara: {str(e)}')
        
        elif action == 'stop':
            try:
                camera_manager.stop_camera(camera_sanitized_name)
                messages.success(request, f'Cámara "{camera_sanitized_name}" detenida')
            except Exception as e:
                messages.error(request, f'Error al detener cámara: {str(e)}')
    
    return redirect('dashboard')

@login_required
@csrf_exempt
def control_all_web(request):
    """Controlar todas las cámaras (iniciar/detener todas)"""
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if 'user_cameras' not in request.session:
            request.session['user_cameras'] = []
        
        if action == 'start':
            started = 0
            for cam in request.session['user_cameras']:
                try:
                    camera_manager.start_camera(cam['sanitized_name'])
                    started += 1
                except Exception as e:
                    print(f"Error iniciando {cam['sanitized_name']}: {e}")
            
            messages.success(request, f'{started} cámaras iniciadas correctamente')
        
        elif action == 'stop':
            stopped = 0
            for cam in request.session['user_cameras']:
                try:
                    camera_manager.stop_camera(cam['sanitized_name'])
                    stopped += 1
                except Exception as e:
                    print(f"Error deteniendo {cam['sanitized_name']}: {e}")
            
            messages.success(request, f'{stopped} cámaras detenidas correctamente')
    
<<<<<<< HEAD
    return redirect('dashboard')
=======
    return redirect('dashboard')

@login_required
@csrf_exempt
def remove_camera_web(request, camera_sanitized_name):
    """Eliminar cámara"""
    if request.method == 'POST':
        try:
            camera_manager.stop_camera(camera_sanitized_name)
            camera_manager.remove_camera(camera_sanitized_name)
            
            user_cameras = request.session.get('user_cameras', [])
            user_cameras = [cam for cam in user_cameras if cam.get('sanitized_name') != camera_sanitized_name]
            request.session['user_cameras'] = user_cameras
            request.session.modified = True
            
            messages.success(request, 'Cámara eliminada')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('dashboard')

# ========== APIs PÚBLICAS ==========

def health_check(request):
    return JsonResponse({
        'status': 'healthy',
        'service': 'Camera Detection System API',
        'yolo_version': '8.0',
        'timestamp': datetime.now().isoformat()
    })

def video_feed(request, camera_sanitized_name):
    """Stream de video CON BOUNDING BOXES de YOLO"""
    def generate_frames():
        while True:
            try:
                # IMPORTANTE: Obtener frame CON bounding boxes
                frame_data = camera_manager.get_camera_frame(camera_sanitized_name, with_boxes=True)
                
                if frame_data:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
                else:
                    # Si no hay frame con boxes, crear uno de placeholder
                    frame = np.zeros((360, 640, 3), dtype=np.uint8)
                    cv2.putText(frame, f'Camera: {camera_sanitized_name}', (50, 180), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    cv2.putText(frame, 'YOLO Processing...', (50, 220), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    _, buffer = cv2.imencode('.jpg', frame)
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                    
            except Exception as e:
                print(f"Error en video feed para {camera_sanitized_name}: {e}")
                # Frame de error
                frame = np.zeros((360, 640, 3), dtype=np.uint8)
                cv2.putText(frame, 'Stream Error', (50, 180), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                _, buffer = cv2.imencode('.jpg', frame)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            
            time.sleep(0.033)  # ~30 FPS
    
    return StreamingHttpResponse(
        generate_frames(),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )

def video_feed_original(request, camera_sanitized_name):
    """Stream de video SIN bounding boxes (frame original)"""
    def generate_frames():
        while True:
            try:
                # Obtener frame SIN bounding boxes
                frame_data = camera_manager.get_camera_frame(camera_sanitized_name, with_boxes=False)
                
                if frame_data:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
                else:
                    # Frame de placeholder
                    frame = np.zeros((360, 640, 3), dtype=np.uint8)
                    cv2.putText(frame, f'Camera: {camera_sanitized_name}', (50, 180), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    cv2.putText(frame, 'Original View', (50, 220), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
                    _, buffer = cv2.imencode('.jpg', frame)
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                    
            except Exception as e:
                print(f"Error en video feed original para {camera_sanitized_name}: {e}")
                frame = np.zeros((360, 640, 3), dtype=np.uint8)
                cv2.putText(frame, 'Stream Error', (50, 180), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                _, buffer = cv2.imencode('.jpg', frame)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            
            time.sleep(0.033)
    
    return StreamingHttpResponse(
        generate_frames(),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )

# ========== NUEVAS APIS PARA DETECCIONES YOLO ==========

def camera_detections_api(request, camera_sanitized_name):
    """API para obtener detecciones reales de YOLO"""
    try:
        limit = int(request.GET.get('limit', 20))
        include_history = request.GET.get('history', 'false').lower() == 'true'
        
        # Obtener detecciones recientes
        recent_detections = camera_manager.get_camera_detections(camera_sanitized_name, limit=limit)
        
        # Opcionalmente incluir historial
        if include_history:
            history = camera_manager.get_detection_history(camera_sanitized_name, limit=50)
        else:
            history = []
        
        # Obtener estadísticas
        stats = camera_manager.get_detection_statistics(camera_sanitized_name)
        
        return JsonResponse({
            'camera_id': camera_sanitized_name,
            'recent_detections': recent_detections,
            'detection_history': history,
            'statistics': stats,
            'count': len(recent_detections),
            'timestamp': datetime.now().isoformat(),
            'success': True
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'success': False
        }, status=500)

def camera_frame_api(request, camera_sanitized_name, boxes=None):
    """API para obtener frame de cámara (con o sin bounding boxes)"""
    try:
        # Determinar si queremos bounding boxes
        if boxes is None:
            boxes = request.GET.get('boxes', 'false').lower() == 'true'
        
        # Obtener frame del camera_manager
        frame_data = camera_manager.get_camera_frame(camera_sanitized_name, with_boxes=boxes)
        
        if frame_data:
            response = HttpResponse(frame_data, content_type='image/jpeg')
            # IMPORTANTE: Deshabilitar cache
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response
        else:
            # Crear imagen por defecto
            frame = np.zeros((360, 640, 3), dtype=np.uint8)
            cv2.putText(frame, f'Camera: {camera_sanitized_name}', (50, 180), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            if boxes:
                cv2.putText(frame, 'Bounding Boxes (YOLO)', (50, 220), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                cv2.putText(frame, 'Original View', (50, 220), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
            
            _, buffer = cv2.imencode('.jpg', frame)
            response = HttpResponse(buffer.tobytes(), content_type='image/jpeg')
            response['Cache-Control'] = 'no-cache'
            return response
            
    except Exception as e:
        # Imagen de error
        frame = np.zeros((360, 640, 3), dtype=np.uint8)
        cv2.putText(frame, f'Error: {str(e)[:50]}', (50, 180), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        _, buffer = cv2.imencode('.jpg', frame)
        response = HttpResponse(buffer.tobytes(), content_type='image/jpeg')
        response['Cache-Control'] = 'no-cache'
        return response

def camera_status_api(request, camera_sanitized_name):
    """API para obtener estado completo de cámara"""
    try:
        camera_status = camera_manager.get_camera_status(camera_sanitized_name)
        
        if not camera_status:
            return JsonResponse({
                'error': 'Camera not found',
                'success': False
            }, status=404)
        
        # Agregar información adicional
        recent_detections = camera_manager.get_camera_detections(camera_sanitized_name, limit=10)
        stats = camera_manager.get_detection_statistics(camera_sanitized_name)
        
        camera_status['recent_detections'] = recent_detections
        camera_status['detection_statistics'] = stats
        camera_status['timestamp'] = datetime.now().isoformat()
        camera_status['success'] = True
        
        return JsonResponse(camera_status)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'success': False
        }, status=500)

def all_cameras_api(request):
    """API para obtener todas las cámaras"""
    try:
        cameras_info = camera_manager.get_cameras_info()
        
        # Agregar detecciones a cada cámara
        for camera in cameras_info:
            camera_id = camera['id']
            camera['recent_detections'] = camera_manager.get_camera_detections(camera_id, limit=5)
            camera['has_boxes'] = camera_manager.get_camera_frame(camera_id, with_boxes=True) is not None
        
        return JsonResponse({
            'cameras': cameras_info,
            'count': len(cameras_info),
            'timestamp': datetime.now().isoformat(),
            'success': True
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'success': False
        }, status=500)

@csrf_exempt
def add_camera_api(request):
    """API para agregar cámara"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            camera_id = data.get('camera_id')
            youtube_url = data.get('youtube_url')
            
            if not camera_id or not youtube_url:
                return JsonResponse({
                    'error': 'camera_id and youtube_url are required',
                    'success': False
                }, status=400)
            
            success = camera_manager.add_camera(camera_id, youtube_url)
            
            if success:
                return JsonResponse({
                    'success': True,
                    'message': f'Camera {camera_id} added successfully',
                    'camera_id': camera_id
                })
            else:
                return JsonResponse({
                    'error': 'Failed to add camera',
                    'success': False
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON',
                'success': False
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'error': str(e),
                'success': False
            }, status=500)
    
    return JsonResponse({
        'error': 'Method not allowed',
        'success': False
    }, status=405)

@csrf_exempt
def start_camera_api(request, camera_id):
    """API para iniciar cámara"""
    if request.method == 'POST':
        try:
            success = camera_manager.start_camera(camera_id)
            
            if success:
                return JsonResponse({
                    'success': True,
                    'message': f'Camera {camera_id} started'
                })
            else:
                return JsonResponse({
                    'error': f'Failed to start camera {camera_id}',
                    'success': False
                }, status=400)
        except Exception as e:
            return JsonResponse({
                'error': str(e),
                'success': False
            }, status=500)
    
    return JsonResponse({
        'error': 'Method not allowed',
        'success': False
    }, status=405)

@csrf_exempt
def stop_camera_api(request, camera_id):
    """API para detener cámara"""
    if request.method == 'POST':
        try:
            camera_manager.stop_camera(camera_id)
            return JsonResponse({
                'success': True,
                'message': f'Camera {camera_id} stopped'
            })
        except Exception as e:
            return JsonResponse({
                'error': str(e),
                'success': False
            }, status=500)
    
    return JsonResponse({
        'error': 'Method not allowed',
        'success': False
    }, status=405)

@csrf_exempt
def remove_camera_api(request, camera_id):
    """API para eliminar cámara"""
    if request.method == 'POST':
        try:
            camera_manager.remove_camera(camera_id)
            return JsonResponse({
                'success': True,
                'message': f'Camera {camera_id} removed'
            })
        except Exception as e:
            return JsonResponse({
                'error': str(e),
                'success': False
            }, status=500)
    
    return JsonResponse({
        'error': 'Method not allowed',
        'success': False
    }, status=405)

# ========== VISTA PARA PRUEBAS YOLO ==========

@login_required
def yolo_test_view(request, camera_sanitized_name):
    """Vista especial para ver detecciones YOLO en tiempo real"""
    try:
        camera_status = camera_manager.get_camera_status(camera_sanitized_name)
        if not camera_status:
            messages.error(request, 'Cámara no encontrada')
            return redirect('dashboard')
        
        # Obtener detecciones recientes
        recent_detections = camera_manager.get_camera_detections(camera_sanitized_name, limit=20)
        detection_stats = camera_manager.get_detection_statistics(camera_sanitized_name)
        
        return render(request, 'detection/yolo_test.html', {
            'camera': camera_status,
            'recent_detections': recent_detections,
            'detection_stats': detection_stats,
            'camera_name': camera_sanitized_name
        })
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('dashboard')
>>>>>>> 94a56a6 (yolo activo!)

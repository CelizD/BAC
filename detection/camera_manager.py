import cv2
import threading
import time
from datetime import datetime
from ultralytics import YOLO
import numpy as np

class CameraManager:
    def __init__(self):
        self.cameras = {}
        self.model = YOLO('yolov8n.pt')
        self.lock = threading.Lock()
    
    def add_camera(self, camera_id, stream_url):
        with self.lock:
            self.cameras[camera_id] = {
                'stream_url': stream_url,
                'status': 'stopped',
                'thread': None,
                'last_detection': None,
                'person_count': 0,
                'last_update': None
            }
    
    def remove_camera(self, camera_id):
        with self.lock:
            if camera_id in self.cameras:
                self.stop_camera(camera_id)
                del self.cameras[camera_id]
    
    def start_camera(self, camera_id):
        with self.lock:
            if camera_id in self.cameras and self.cameras[camera_id]['status'] == 'stopped':
                self.cameras[camera_id]['status'] = 'starting'
                thread = threading.Thread(target=self._process_stream, args=(camera_id,))
                self.cameras[camera_id]['thread'] = thread
                thread.start()
    
    def stop_camera(self, camera_id):
        with self.lock:
            if camera_id in self.cameras:
                self.cameras[camera_id]['status'] = 'stopped'
    
    def _process_stream(self, camera_id):
        camera = self.cameras[camera_id]
        stream_url = camera['stream_url']
        
        # Intentar conectar a la cámara
        cap = cv2.VideoCapture(stream_url)
        
        if not cap.isOpened():
            camera['status'] = 'error'
            return
        
        camera['status'] = 'running'
        
        while self.cameras.get(camera_id, {}).get('status') == 'running':
            ret, frame = cap.read()
            
            if not ret:
                time.sleep(1)
                continue
            
            # Detección con YOLO
            results = self.model(frame, verbose=False)
            
            # Contar personas (clase 0 en COCO)
            person_count = 0
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        cls = int(box.cls[0])
                        if cls == 0:  # Person class
                            person_count += 1
            
            # Actualizar estado
            with self.lock:
                if camera_id in self.cameras:
                    self.cameras[camera_id]['person_count'] = person_count
                    self.cameras[camera_id]['last_update'] = datetime.now().isoformat()
                    self.cameras[camera_id]['last_detection'] = datetime.now().isoformat()
            
            time.sleep(0.1)  # Controlar FPS
        
        cap.release()
        camera['status'] = 'stopped'
    
    def get_cameras_info(self):
        with self.lock:
            cameras_info = []
            for camera_id, camera_data in self.cameras.items():
                cameras_info.append({
                    'id': camera_id,
                    'name': camera_id,
                    'stream_url': camera_data['stream_url'],
                    'status': camera_data['status'],
                    'person_count': camera_data['person_count'],
                    'last_update': camera_data['last_update']
                })
            return cameras_info
    
    def get_camera_status(self, camera_id):
        with self.lock:
            if camera_id in self.cameras:
                return self.cameras[camera_id]
            return None
    
    def start_all_cameras(self):
        with self.lock:
            for camera_id in self.cameras:
                self.start_camera(camera_id)
    
    def stop_all_cameras(self):
        with self.lock:
            for camera_id in self.cameras:
                self.stop_camera(camera_id)
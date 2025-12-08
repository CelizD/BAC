<<<<<<< HEAD
# detection/camera_manager.py
=======
# detection/camera_manager.py - VERSIÓN SIN EMULACIÓN
>>>>>>> 94a56a6 (yolo activo!)
import threading
import time
import io
from datetime import datetime
import traceback

try:
    import cv2
except Exception:
    cv2 = None

import numpy as np
<<<<<<< HEAD
import random
=======
>>>>>>> 94a56a6 (yolo activo!)
import logging

logger = logging.getLogger(__name__)

<<<<<<< HEAD
# Optional: if ultralytics is installed, we'll try to use it
DETECTION_ENABLED = False
YOLO_MODEL = None
YOLO_MODEL_PATH = "yolov8n.pt"  # default; asegúrate que exista o se descargará por ultralytics
=======
# YOLO detection - REAL, NO MOCK
DETECTION_ENABLED = False
YOLO_MODEL = None
YOLO_MODEL_PATH = "yolov8n.pt"
>>>>>>> 94a56a6 (yolo activo!)

try:
    from ultralytics import YOLO
    try:
        YOLO_MODEL = YOLO(YOLO_MODEL_PATH)
        DETECTION_ENABLED = True
<<<<<<< HEAD
        logger.info("Ultralytics YOLO cargado correctamente.")
    except Exception as e:
        logger.warning(f"No se pudo cargar el modelo YOLO: {e}\nSe trabajará con detecciones mock.")
        DETECTION_ENABLED = False
except Exception:
    logger.info("ultralytics no está instalado; usando detecciones mock.")
=======
        logger.info("✅ Ultralytics YOLO cargado correctamente - DETECCIÓN REAL HABILITADA")
    except Exception as e:
        logger.error(f"❌ No se pudo cargar el modelo YOLO: {e}")
        logger.error("⚠️ INSTALA YOLO PARA USAR DETECCIÓN REAL")
        DETECTION_ENABLED = False
except Exception:
    logger.error("❌ ultralytics no está instalado")
    logger.error("⚠️ Instala con: pip install ultralytics")
>>>>>>> 94a56a6 (yolo activo!)
    DETECTION_ENABLED = False


class Camera:
    def __init__(self, camera_id: str, source: str, detection_interval: float = 1.0):
        """
<<<<<<< HEAD
        source: ruta RTSP, HTTP, archivo local o Youtube/stream (si es compatible con VideoCapture)
=======
        source: ruta RTSP, HTTP, archivo local o stream compatible con VideoCapture
>>>>>>> 94a56a6 (yolo activo!)
        """
        self.camera_id = camera_id
        self.source = source
        self.detection_interval = detection_interval
        self._capture = None
        self._thread = None
        self._running = False
        self._lock = threading.RLock()
        self.last_frame = None          # JPEG bytes
        self.last_frame_ts = None
<<<<<<< HEAD
        self.last_detections = []       # list of detection dicts
=======
        self.last_detections = []       # SOLO detecciones REALES de YOLO
>>>>>>> 94a56a6 (yolo activo!)
        self.last_error = None
        self.fps = 0.0
        self._last_detection_time = 0.0

    def start(self):
        with self._lock:
            if self._running:
                return True
            self._running = True
            self._thread = threading.Thread(target=self._loop, name=f"CameraThread-{self.camera_id}", daemon=True)
            self._thread.start()
            logger.info(f"Camera {self.camera_id} thread started.")
            return True

    def stop(self):
        with self._lock:
            if not self._running:
                return True
            self._running = False
<<<<<<< HEAD
        # wait for thread to finish
        if self._thread:
            self._thread.join(timeout=2.0)
        # release capture
=======
        if self._thread:
            self._thread.join(timeout=2.0)
>>>>>>> 94a56a6 (yolo activo!)
        if self._capture:
            try:
                self._capture.release()
            except Exception:
                pass
            self._capture = None
        logger.info(f"Camera {self.camera_id} stopped.")
        return True

    def _open_capture(self):
        if cv2 is None:
            raise RuntimeError("cv2 no disponible. Instala opencv-python(-headless).")
<<<<<<< HEAD
        # Try to open capture; allow retries
        # If source is numeric string, try as index
=======
        
>>>>>>> 94a56a6 (yolo activo!)
        attempts = 0
        while attempts < 3:
            try:
                src = self.source
<<<<<<< HEAD
                # if source looks like an int index
                if isinstance(src, str) and src.isdigit():
                    src = int(src)
                cap = cv2.VideoCapture(src, cv2.CAP_ANY)
                # small wait for camera to warm
=======
                if isinstance(src, str) and src.isdigit():
                    src = int(src)
                cap = cv2.VideoCapture(src, cv2.CAP_ANY)
>>>>>>> 94a56a6 (yolo activo!)
                time.sleep(0.3)
                if cap is not None and cap.isOpened():
                    return cap
                else:
                    try:
                        cap.release()
                    except Exception:
                        pass
            except Exception:
                logger.debug("error opening capture", exc_info=True)
            attempts += 1
            time.sleep(0.5)
        raise RuntimeError(f"No se pudo abrir VideoCapture para {self.source}")

    def _loop(self):
        try:
            self._capture = self._open_capture()
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"[{self.camera_id}] Error al abrir la fuente: {e}")
            self._running = False
            return

        read_start = time.time()
        frame_count = 0

        while self._running:
            try:
                t0 = time.time()
                ret, frame = self._capture.read()
                if not ret or frame is None:
<<<<<<< HEAD
                    # no frame, try reopen once
=======
>>>>>>> 94a56a6 (yolo activo!)
                    logger.warning(f"[{self.camera_id}] No frame recibido. Intentando reconectar...")
                    try:
                        self._capture.release()
                    except Exception:
                        pass
                    time.sleep(0.5)
                    try:
                        self._capture = self._open_capture()
                        continue
                    except Exception as e:
                        self.last_error = str(e)
                        logger.error(f"[{self.camera_id}] Reconexión fallida: {e}")
                        time.sleep(1.0)
                        continue

                frame_count += 1
<<<<<<< HEAD
                # update fps roughly
=======
>>>>>>> 94a56a6 (yolo activo!)
                elapsed = time.time() - read_start
                if elapsed > 0:
                    self.fps = frame_count / elapsed

<<<<<<< HEAD
                # encode to JPEG and save
=======
                # Encode to JPEG
>>>>>>> 94a56a6 (yolo activo!)
                try:
                    _, buf = cv2.imencode('.jpg', frame)
                    jpeg_bytes = buf.tobytes()
                    with self._lock:
                        self.last_frame = jpeg_bytes
                        self.last_frame_ts = datetime.utcnow().isoformat() + "Z"
                except Exception as e:
                    logger.exception(f"[{self.camera_id}] Error al codificar frame JPEG: {e}")

<<<<<<< HEAD
                # detection (run only every detection_interval)
=======
                # DETECCIÓN REAL (solo cada detection_interval)
>>>>>>> 94a56a6 (yolo activo!)
                now = time.time()
                if (now - self._last_detection_time) >= self.detection_interval:
                    self._last_detection_time = now
                    try:
                        detections = self._run_detection(frame)
                        with self._lock:
                            self.last_detections = detections
                    except Exception as e:
                        logger.exception(f"[{self.camera_id}] Error en detección: {e}")
                        with self._lock:
                            self.last_detections = []

<<<<<<< HEAD
                # small sleep to avoid tight loop
                # aim to keep loop responsive but not 100% CPU
=======
>>>>>>> 94a56a6 (yolo activo!)
                time.sleep(0.01)

            except Exception as e:
                logger.exception(f"[{self.camera_id}] Error en loop de captura: {e}")
                self.last_error = str(e)
                time.sleep(1.0)

<<<<<<< HEAD
        # cleanup when leaving loop
=======
>>>>>>> 94a56a6 (yolo activo!)
        try:
            if self._capture:
                self._capture.release()
        except Exception:
            pass

    def _run_detection(self, frame):
        """
<<<<<<< HEAD
        Ejecuta detección sobre el frame (BGR numpy array).
        Devuelve lista de detections en formato:
        [{'id': str, 'label': str, 'confidence': float, 'bbox': [x1,y1,x2,y2]}...]
        """
        detections = []

        if DETECTION_ENABLED and YOLO_MODEL is not None:
            try:
                # ultralytics expects RGB
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = YOLO_MODEL(rgb)  # quick inference; model handles batching
                # results may contain multiple frames; we take first
                for r in results:
                    boxes = r.boxes
                    if boxes is None:
                        continue
                    for b in boxes:
                        # depending on ultralytics version, b may have .xyxy, .conf, .cls
                        try:
                            xyxy = b.xyxy[0].tolist() if hasattr(b, 'xyxy') else b.xyxy.tolist()
                        except Exception:
                            try:
                                xyxy = list(map(float, b.xyxy))
                            except Exception:
                                xyxy = [0, 0, 0, 0]
                        conf = float(b.conf[0]) if hasattr(b, 'conf') else float(b.conf)
                        cls = int(b.cls[0]) if hasattr(b, 'cls') else int(b.cls)
                        label = YOLO_MODEL.names.get(cls, str(cls)) if hasattr(YOLO_MODEL, 'names') else str(cls)
                        detections.append({
                            'id': f"{self.camera_id}_{int(time.time()*1000)}_{len(detections)}",
                            'label': label,
                            'confidence': round(conf, 4),
                            'bbox': [int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])],
                        })
                return detections
            except Exception:
                # fallback to mock below
                logger.exception(f"[{self.camera_id}] fallo en ultralytics detection, uso mock")
        # Mock detections if no model
        h, w = frame.shape[:2] if hasattr(frame, 'shape') else (360, 640)
        for i in range(random.randint(0, 3)):
            x1 = random.randint(0, max(0, w - 100))
            y1 = random.randint(0, max(0, h - 100))
            x2 = x1 + random.randint(40, 160)
            y2 = y1 + random.randint(60, 240)
            detections.append({
                'id': f"{self.camera_id}_{int(time.time()*1000)}_{i}",
                'label': random.choice(['person', 'car', 'bicycle']),
                'confidence': round(0.5 + random.random() * 0.5, 3),
                'bbox': [x1, y1, min(x2, w-1), min(y2, h-1)]
            })
        return detections
=======
        ⚠️ SOLO DETECCIONES REALES - NO MOCK
        Si YOLO no está disponible, retorna lista vacía
        """
        detections = []

        if not DETECTION_ENABLED or YOLO_MODEL is None:
            logger.warning(f"[{self.camera_id}] ⚠️ YOLO no disponible - NO hay detección")
            return []  # ← SIN DATOS FALSOS

        # DETECCIÓN REAL CON YOLO
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = YOLO_MODEL(rgb, verbose=False)
            
            for r in results:
                boxes = r.boxes
                if boxes is None:
                    continue
                for b in boxes:
                    try:
                        xyxy = b.xyxy[0].tolist() if hasattr(b, 'xyxy') else b.xyxy.tolist()
                    except Exception:
                        try:
                            xyxy = list(map(float, b.xyxy))
                        except Exception:
                            xyxy = [0, 0, 0, 0]
                    
                    conf = float(b.conf[0]) if hasattr(b, 'conf') else float(b.conf)
                    cls = int(b.cls[0]) if hasattr(b, 'cls') else int(b.cls)
                    label = YOLO_MODEL.names.get(cls, str(cls)) if hasattr(YOLO_MODEL, 'names') else str(cls)
                    
                    detections.append({
                        'id': f"{self.camera_id}_{int(time.time()*1000)}_{len(detections)}",
                        'label': label,
                        'confidence': round(conf, 4),
                        'bbox': [int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])],
                        'timestamp': datetime.utcnow().isoformat() + "Z"
                    })
            
            logger.info(f"[{self.camera_id}] ✅ Detección REAL: {len(detections)} objetos encontrados")
            return detections
            
        except Exception as e:
            logger.exception(f"[{self.camera_id}] ❌ Error en YOLO detection: {e}")
            return []  # ← Si falla, retorna vacío, NO datos falsos
>>>>>>> 94a56a6 (yolo activo!)


class CameraManager:
    def __init__(self):
<<<<<<< HEAD
        self.cameras = {}  # camera_id -> Camera
        self._lock = threading.RLock()
=======
        self.cameras = {}
        self._lock = threading.RLock()
        
        # Advertencia si YOLO no está disponible
        if not DETECTION_ENABLED:
            logger.warning("="*60)
            logger.warning("⚠️  YOLO NO DISPONIBLE - DETECCIÓN DESHABILITADA")
            logger.warning("⚠️  Instala con: pip install ultralytics")
            logger.warning("⚠️  Las cámaras capturarán video pero SIN detección")
            logger.warning("="*60)
>>>>>>> 94a56a6 (yolo activo!)

    def add_camera(self, camera_id: str, source: str) -> bool:
        with self._lock:
            if camera_id in self.cameras:
                logger.warning(f"add_camera: {camera_id} ya existe")
                return False
            cam = Camera(camera_id, source)
            self.cameras[camera_id] = cam
<<<<<<< HEAD
            logger.info(f"Cámara añadida: {camera_id} -> {source}")
=======
            logger.info(f"📹 Cámara añadida: {camera_id} -> {source}")
>>>>>>> 94a56a6 (yolo activo!)
            return True

    def start_camera(self, camera_id: str) -> bool:
        with self._lock:
            cam = self.cameras.get(camera_id)
            if not cam:
                logger.warning(f"start_camera: {camera_id} no encontrada")
                return False
            return cam.start()

    def stop_camera(self, camera_id: str) -> bool:
        with self._lock:
            cam = self.cameras.get(camera_id)
            if not cam:
                return False
            return cam.stop()

    def remove_camera(self, camera_id: str) -> bool:
        with self._lock:
            cam = self.cameras.pop(camera_id, None)
        if cam:
            try:
                cam.stop()
            except Exception:
                pass
            logger.info(f"Cámara {camera_id} eliminada")
            return True
        return False

    def get_camera_status(self, camera_id: str):
        cam = self.cameras.get(camera_id)
        if not cam:
<<<<<<< HEAD
            return None
        with cam._lock:
            return {
                'camera_id': cam.camera_id,
                'source': cam.source,
                'running': cam._running,
                'last_frame_ts': cam.last_frame_ts,
                'last_error': cam.last_error,
                'fps': round(cam.fps, 2),
                'detections_count': len(cam.last_detections),
            }

    def get_camera_frame(self, camera_id: str):
        cam = self.cameras.get(camera_id)
        if not cam:
            return None
        with cam._lock:
            return cam.last_frame

    def get_camera_detections(self, camera_id: str):
        cam = self.cameras.get(camera_id)
        if not cam:
            return []
        with cam._lock:
            return list(cam.last_detections)

=======
            return None
        with cam._lock:
            return {
                'camera_id': cam.camera_id,
                'source': cam.source,
                'running': cam._running,
                'last_frame_ts': cam.last_frame_ts,
                'last_error': cam.last_error,
                'fps': round(cam.fps, 2),
                'detections_count': len(cam.last_detections),
                'yolo_enabled': DETECTION_ENABLED  # ← Indica si hay detección real
            }

    def get_camera_frame(self, camera_id: str, with_boxes: bool = False):
        """
        Obtiene el frame de la cámara
        Si with_boxes=True, dibuja los bounding boxes de las detecciones REALES
        """
        cam = self.cameras.get(camera_id)
        if not cam:
            return None
        
        with cam._lock:
            if not with_boxes:
                return cam.last_frame
            
            # Dibujar bounding boxes SOLO si hay detecciones REALES
            if cam.last_frame and cam.last_detections:
                try:
                    # Decodificar JPEG
                    nparr = np.frombuffer(cam.last_frame, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    # Dibujar cada detección REAL
                    for det in cam.last_detections:
                        bbox = det.get('bbox', [])
                        if len(bbox) == 4:
                            x1, y1, x2, y2 = bbox
                            label = det.get('label', 'unknown')
                            conf = det.get('confidence', 0.0)
                            
                            # Dibujar rectángulo
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            
                            # Dibujar etiqueta
                            text = f"{label} {conf:.2f}"
                            cv2.putText(frame, text, (x1, y1-10), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    
                    # Recodificar a JPEG
                    _, buf = cv2.imencode('.jpg', frame)
                    return buf.tobytes()
                    
                except Exception as e:
                    logger.error(f"Error dibujando boxes: {e}")
            
            return cam.last_frame

    def get_camera_detections(self, camera_id: str, limit: int = 20):
        """Retorna SOLO detecciones REALES"""
        cam = self.cameras.get(camera_id)
        if not cam:
            return []
        with cam._lock:
            detections = list(cam.last_detections)
            return detections[:limit] if limit else detections

    def get_detection_statistics(self, camera_id: str):
        """Estadísticas de detecciones REALES"""
        cam = self.cameras.get(camera_id)
        if not cam:
            return {}
        
        with cam._lock:
            detections = cam.last_detections
            
            if not detections:
                return {
                    'total_detections': 0,
                    'avg_confidence': 0.0,
                    'yolo_enabled': DETECTION_ENABLED
                }
            
            total = len(detections)
            avg_conf = sum(d.get('confidence', 0) for d in detections) / total if total > 0 else 0
            
            return {
                'total_detections': total,
                'avg_confidence': round(avg_conf, 3),
                'yolo_enabled': DETECTION_ENABLED,
                'labels': list(set(d.get('label', 'unknown') for d in detections))
            }

>>>>>>> 94a56a6 (yolo activo!)
    def get_cameras_info(self):
        with self._lock:
            out = []
            for cid, cam in self.cameras.items():
<<<<<<< HEAD
                out.append(self.get_camera_status(cid))
            return out


# single global instance
camera_manager = CameraManager()

# optional: preload a demo camera if none exists (commented)
# camera_manager.add_camera("demo", 0)
# camera_manager.start_camera("demo")
=======
                status = self.get_camera_status(cid)
                if status:
                    # Agregar contador de personas (solo objetos de clase 'person')
                    person_count = sum(1 for d in cam.last_detections if d.get('label') == 'person')
                    status['person_count'] = person_count
                    out.append(status)
            return out


# Instancia global
camera_manager = CameraManager()
>>>>>>> 94a56a6 (yolo activo!)

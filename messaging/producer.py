# messaging/producer.py
import pika
import json
from datetime import datetime
from django.conf import settings

class RabbitMQProducer:
    def __init__(self):
        credentials = pika.PlainCredentials(
            settings.RABBITMQ_USER,
            settings.RABBITMQ_PASSWORD
        )
        parameters = pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            credentials=credentials
        )
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        
        # Declarar colas
        self.channel.queue_declare(queue='camera_events', durable=True)
        self.channel.queue_declare(queue='detection_results', durable=True)
        self.channel.queue_declare(queue='occupancy_alerts', durable=True)
    
    def publish_camera_started(self, camera_name, stream_url):
        """Publicar evento cuando se inicia una cámara"""
        message = {
            'event': 'camera_started',
            'camera_name': camera_name,
            'stream_url': stream_url,
            'timestamp': datetime.now().isoformat()
        }
        self._publish('camera_events', message)
    
    def publish_detection_result(self, camera_name, person_count, chair_count, occupancy_rate):
        """Publicar resultado de detección YOLO"""
        message = {
            'camera_name': camera_name,
            'person_count': person_count,
            'chair_count': chair_count,
            'occupancy_rate': occupancy_rate,
            'timestamp': datetime.now().isoformat()
        }
        self._publish('detection_results', message)
    
    def publish_occupancy_alert(self, camera_name, occupancy_rate, threshold=80):
        """Publicar alerta si ocupación es alta"""
        if occupancy_rate >= threshold:
            message = {
                'alert_type': 'high_occupancy',
                'camera_name': camera_name,
                'occupancy_rate': occupancy_rate,
                'threshold': threshold,
                'timestamp': datetime.now().isoformat()
            }
            self._publish('occupancy_alerts', message)
    
    def _publish(self, queue_name, message):
        """Método interno para publicar mensajes"""
        self.channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Mensaje persistente
                content_type='application/json'
            )
        )
        print(f"📤 Mensaje publicado a '{queue_name}': {message}")
    
    def close(self):
        """Cerrar conexión"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
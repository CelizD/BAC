# messaging/consumer.py
import pika
import json
from django.conf import settings

class RabbitMQConsumer:
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
        
        # Declarar colas (por si no existen)
        self.channel.queue_declare(queue='camera_events', durable=True)
        self.channel.queue_declare(queue='detection_results', durable=True)
        self.channel.queue_declare(queue='occupancy_alerts', durable=True)
    
    def callback_camera_events(self, ch, method, properties, body):
        """Procesar eventos de cámaras"""
        message = json.loads(body)
        print(f"📥 Evento de cámara recibido: {message}")
        
        # Aquí podrías guardar en logs, enviar notificaciones, etc.
        if message['event'] == 'camera_started':
            print(f"✅ Cámara '{message['camera_name']}' iniciada en {message['timestamp']}")
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
    
    def callback_detection_results(self, ch, method, properties, body):
        """Procesar resultados de detección"""
        message = json.loads(body)
        print(f"📊 Detección recibida: {message['camera_name']} - "
              f"{message['person_count']} personas ({message['occupancy_rate']}% ocupación)")
        
        # Aquí podrías:
        # - Guardar en base de datos
        # - Generar gráficos
        # - Enviar a otro sistema
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
    
    def callback_occupancy_alerts(self, ch, method, properties, body):
        """Procesar alertas de ocupación alta"""
        message = json.loads(body)
        print(f"🚨 ALERTA: {message['camera_name']} tiene {message['occupancy_rate']}% ocupación!")
        
        # Aquí podrías:
        # - Enviar email
        # - Notificación push
        # - SMS
        # - Webhook a otro sistema
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
    
    def start_consuming(self, queue_name='detection_results'):
        """Iniciar consumidor para una cola específica"""
        callback_map = {
            'camera_events': self.callback_camera_events,
            'detection_results': self.callback_detection_results,
            'occupancy_alerts': self.callback_occupancy_alerts
        }
        
        callback = callback_map.get(queue_name, self.callback_detection_results)
        
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback
        )
        
        print(f'🎧 Esperando mensajes en cola "{queue_name}"...')
        print('Presiona CTRL+C para salir')
        self.channel.start_consuming()
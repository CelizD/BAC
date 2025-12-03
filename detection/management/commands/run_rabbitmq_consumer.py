# detection/management/commands/run_rabbitmq_consumer.py
from django.core.management.base import BaseCommand
from messaging.consumer import RabbitMQConsumer

class Command(BaseCommand):
    help = 'Ejecuta el consumidor de RabbitMQ'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--queue',
            type=str,
            default='detection_results',
            help='Nombre de la cola a consumir'
        )
    
    def handle(self, *args, **options):
        queue_name = options['queue']
        self.stdout.write(f'Iniciando consumidor para cola: {queue_name}')
        
        try:
            consumer = RabbitMQConsumer()
            consumer.start_consuming(queue_name)
        except KeyboardInterrupt:
            self.stdout.write('Consumidor detenido')
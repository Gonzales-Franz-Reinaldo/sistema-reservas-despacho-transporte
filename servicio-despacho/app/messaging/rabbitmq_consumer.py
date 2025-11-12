import pika
import json
import logging
from typing import Callable
from app.config import settings
from app.models.database import SessionLocal
from app.services.asignacion_service import AsignacionService
from app.schemas.schemas import SolicitudViajeEvent, AsignacionCompletadaEvent
from app.messaging.rabbitmq_publisher import RabbitMQPublisher

logger = logging.getLogger(__name__)


class RabbitMQConsumer:
    """Consumidor de mensajes de RabbitMQ"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.publisher = RabbitMQPublisher()
    
    def connect(self):
        """Establece conexión con RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(
                settings.RABBITMQ_USER,
                settings.RABBITMQ_PASSWORD
            )
            
            parameters = pika.ConnectionParameters(
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT,
                virtual_host=settings.RABBITMQ_VHOST,
                credentials=credentials
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declarar exchange
            self.channel.exchange_declare(
                exchange=settings.EXCHANGE_VIAJES,
                exchange_type='topic',
                durable=True
            )
            
            # Declarar colas
            self.channel.queue_declare(
                queue=settings.QUEUE_NUEVAS_RESERVAS,
                durable=True
            )
            
            self.channel.queue_declare(
                queue=settings.QUEUE_ASIGNACIONES_COMPLETADAS,
                durable=True
            )
            
            # Bind de la cola al exchange
            self.channel.queue_bind(
                exchange=settings.EXCHANGE_VIAJES,
                queue=settings.QUEUE_NUEVAS_RESERVAS,
                routing_key='viaje.creado'
            )
            
            logger.info("Conexión a RabbitMQ establecida")
            
        except Exception as e:
            logger.error(f"Error conectando a RabbitMQ: {str(e)}")
            raise
    
    def procesar_nueva_reserva(self, ch, method, properties, body):
        """
        Callback que procesa mensajes de nuevas reservas
        """
        db = SessionLocal()
        try:
            # Decodificar el mensaje
            mensaje = json.loads(body.decode('utf-8'))
            logger.info(f"Nueva reserva recibida: {mensaje}")
            
            # Validar y convertir a schema
            solicitud = SolicitudViajeEvent(**mensaje)
            
            # Asignar conductor usando el servicio
            asignacion = AsignacionService.asignar_conductor_por_cercania(db, solicitud)
            
            if asignacion:
                # Calcular datos adicionales
                conductor = db.query(AsignacionService).filter_by(
                    id_conductor=asignacion.id_conductor
                ).first()
                
                # Crear evento de asignación completada
                evento_asignacion = AsignacionCompletadaEvent(
                    id_viaje=asignacion.id_viaje,
                    id_conductor=asignacion.id_conductor,
                    id_asignacion=asignacion.id_asignacion,
                    fecha_asignacion=asignacion.fecha_asignacion,
                    distancia_conductor=None,
                    tiempo_estimado_llegada=None
                )
                
                # Publicar evento de asignación completada
                self.publisher.publicar_asignacion_completada(evento_asignacion)
                
                # Confirmar mensaje
                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.info(f"Asignación completada para viaje {solicitud.id_viaje}")
            else:
                # No hay conductores disponibles - reencolar mensaje
                logger.warning(f"No hay conductores disponibles para viaje {solicitud.id_viaje}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        
        except Exception as e:
            logger.error(f"Error procesando reserva: {str(e)}")
            # Rechazar mensaje sin reencolar si hay error de validación
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
        finally:
            db.close()
    
    def iniciar_consumo(self):
        """Inicia el consumo de mensajes"""
        try:
            self.connect()
            
            # Configurar QoS (procesar 1 mensaje a la vez)
            self.channel.basic_qos(prefetch_count=1)
            
            # Configurar callback
            self.channel.basic_consume(
                queue=settings.QUEUE_NUEVAS_RESERVAS,
                on_message_callback=self.procesar_nueva_reserva
            )
            
            logger.info("Esperando mensajes de nuevas reservas...")
            self.channel.start_consuming()
        
        except KeyboardInterrupt:
            logger.info("Consumo interrumpido por el usuario")
            self.cerrar()
        except Exception as e:
            logger.error(f"Error en el consumo: {str(e)}")
            raise
    
    def cerrar(self):
        """Cierra la conexión"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("Conexión a RabbitMQ cerrada")
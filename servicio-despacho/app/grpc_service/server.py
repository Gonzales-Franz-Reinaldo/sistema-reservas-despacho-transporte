import grpc
from concurrent import futures
import logging
from datetime import datetime

# Importar los protobuf generados (se generarán después)
from app.grpc_service.protos import despacho_pb2, despacho_pb2_grpc

from app.models.database import SessionLocal, DisponibilidadConductor, EstadoConductor
from app.services.asignacion_service import AsignacionService
from app.schemas.schemas import SolicitudViajeEvent, PrioridadEnum
from app.config import settings

logger = logging.getLogger(__name__)


class DespachoServicer(despacho_pb2_grpc.DespachoServiceServicer):
    """Implementación del servicio gRPC"""
    
    def AsignarConductor(self, request, context):
        """Asigna un conductor a un viaje"""
        db = SessionLocal()
        try:
            logger.info(f"Solicitud de asignación recibida para viaje {request.id_viaje}")
            
            # Convertir request a schema
            solicitud = SolicitudViajeEvent(
                id_viaje=request.id_viaje,
                id_cliente=request.id_cliente,
                punto_origen_lat=request.origen_lat,
                punto_origen_lon=request.origen_lon,
                punto_destino_lat=request.destino_lat,
                punto_destino_lon=request.destino_lon,
                prioridad=PrioridadEnum(request.prioridad) if request.prioridad else PrioridadEnum.MEDIA
            )
            
            # Asignar conductor
            asignacion = AsignacionService.asignar_conductor_por_cercania(db, solicitud)
            
            if asignacion:
                # Calcular distancia y tiempo estimado
                conductor = db.query(DisponibilidadConductor).filter(
                    DisponibilidadConductor.id_conductor == asignacion.id_conductor
                ).first()
                
                distancia = AsignacionService.calcular_distancia(
                    request.origen_lat, request.origen_lon,
                    conductor.ubicacion_latitud, conductor.ubicacion_longitud
                )
                tiempo_estimado = AsignacionService.estimar_tiempo_llegada(distancia)
                
                return despacho_pb2.RespuestaAsignacion(
                    exitoso=True,
                    mensaje=f"Conductor {asignacion.id_conductor} asignado exitosamente",
                    id_conductor=asignacion.id_conductor,
                    id_asignacion=asignacion.id_asignacion,
                    distancia_conductor=distancia,
                    tiempo_estimado_llegada=tiempo_estimado
                )
            else:
                logger.warning(f"No se pudo asignar conductor para viaje {request.id_viaje}")
                return despacho_pb2.RespuestaAsignacion(
                    exitoso=False,
                    mensaje="No hay conductores disponibles en este momento",
                    id_conductor=0,
                    id_asignacion=0,
                    distancia_conductor=0.0,
                    tiempo_estimado_llegada=0
                )
        
        except Exception as e:
            logger.error(f"Error en asignación: {str(e)}")
            return despacho_pb2.RespuestaAsignacion(
                exitoso=False,
                mensaje=f"Error en la asignación: {str(e)}",
                id_conductor=0,
                id_asignacion=0
            )
        finally:
            db.close()
    
    def ObtenerEstadoConductor(self, request, context):
        """Obtiene el estado actual de un conductor"""
        db = SessionLocal()
        try:
            conductor = db.query(DisponibilidadConductor).filter(
                DisponibilidadConductor.id_conductor == request.id_conductor
            ).first()
            
            if conductor:
                return despacho_pb2.RespuestaEstadoConductor(
                    id_conductor=conductor.id_conductor,
                    estado=conductor.estado.value,
                    ubicacion_lat=conductor.ubicacion_latitud or 0.0,
                    ubicacion_lon=conductor.ubicacion_longitud or 0.0,
                    ultima_actualizacion=conductor.ultima_actualizacion.isoformat()
                )
            else:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Conductor {request.id_conductor} no encontrado")
                return despacho_pb2.RespuestaEstadoConductor()
        
        finally:
            db.close()
    
    def ActualizarDisponibilidad(self, request, context):
        """Actualiza la disponibilidad y ubicación de un conductor"""
        db = SessionLocal()
        try:
            conductor = db.query(DisponibilidadConductor).filter(
                DisponibilidadConductor.id_conductor == request.id_conductor
            ).first()
            
            if not conductor:
                # Crear nuevo conductor si no existe
                conductor = DisponibilidadConductor(
                    id_conductor=request.id_conductor,
                    estado=EstadoConductor[request.estado.upper()],
                    ubicacion_latitud=request.ubicacion_lat,
                    ubicacion_longitud=request.ubicacion_lon
                )
                db.add(conductor)
            else:
                # Actualizar conductor existente
                conductor.estado = EstadoConductor[request.estado.upper()]
                conductor.ubicacion_latitud = request.ubicacion_lat
                conductor.ubicacion_longitud = request.ubicacion_lon
            
            db.commit()
            
            return despacho_pb2.RespuestaActualizacion(
                exitoso=True,
                mensaje=f"Disponibilidad del conductor {request.id_conductor} actualizada"
            )
        
        except Exception as e:
            logger.error(f"Error actualizando disponibilidad: {str(e)}")
            return despacho_pb2.RespuestaActualizacion(
                exitoso=False,
                mensaje=f"Error: {str(e)}"
            )
        finally:
            db.close()


def serve():
    """Inicia el servidor gRPC"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    despacho_pb2_grpc.add_DespachoServiceServicer_to_server(DespachoServicer(), server)
    
    server_address = f"[::]:{settings.GRPC_PORT}"
    server.add_insecure_port(server_address)
    
    logger.info(f"Servidor gRPC iniciado en {server_address}")
    server.start()
    server.wait_for_termination()
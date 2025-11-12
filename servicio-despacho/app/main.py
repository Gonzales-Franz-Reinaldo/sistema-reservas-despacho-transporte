from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import threading

from app.config import settings
from app.api.routes import router
from app.models.database import create_tables
from app.messaging.rabbitmq_consumer import RabbitMQConsumer
from app.grpc_service.server import serve as grpc_serve

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION,
    description="Servicio de Despacho - Asignación de Conductores",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas
app.include_router(router, prefix="/api/v1", tags=["despacho"])


# Eventos de inicio y cierre
@app.on_event("startup")
async def startup_event():
    """Evento que se ejecuta al iniciar la aplicación"""
    logger.info(f"Iniciando {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")
    
    # Crear tablas en la base de datos
    try:
        create_tables()
        logger.info("Tablas de base de datos verificadas/creadas")
    except Exception as e:
        logger.error(f"Error creando tablas: {str(e)}")
    
    # Iniciar servidor gRPC en un hilo separado
    grpc_thread = threading.Thread(target=grpc_serve, daemon=True)
    grpc_thread.start()
    logger.info(f"Servidor gRPC iniciado en puerto {settings.GRPC_PORT}")
    
    # Iniciar consumidor de RabbitMQ en un hilo separado
    def start_rabbitmq_consumer():
        consumer = RabbitMQConsumer()
        try:
            consumer.iniciar_consumo()
        except Exception as e:
            logger.error(f"Error en consumidor RabbitMQ: {str(e)}")
    
    rabbitmq_thread = threading.Thread(target=start_rabbitmq_consumer, daemon=True)
    rabbitmq_thread.start()
    logger.info("Consumidor de RabbitMQ iniciado")


@app.on_event("shutdown")
async def shutdown_event():
    """Evento que se ejecuta al cerrar la aplicación"""
    logger.info(f"Cerrando {settings.SERVICE_NAME}")


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True if settings.ENVIRONMENT == "development" else False
    )
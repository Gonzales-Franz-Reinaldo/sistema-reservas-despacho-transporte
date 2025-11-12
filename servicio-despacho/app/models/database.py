from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

from app.config import settings

# Motor de base de datos
engine = create_engine(settings.DATABASE_URL, echo=settings.DB_ECHO)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Enums
class EstadoConductor(enum.Enum):
    DISPONIBLE = "disponible"
    OCUPADO = "ocupado"
    INACTIVO = "inactivo"


class PrioridadAsignacion(enum.Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


# Modelos
class DisponibilidadConductor(Base):
    """Tabla: disponibilidad_conductores"""
    __tablename__ = "disponibilidad_conductores"
    
    id_conductor = Column(Integer, primary_key=True, index=True)
    estado = Column(SQLEnum(EstadoConductor), default=EstadoConductor.DISPONIBLE, nullable=False)
    ubicacion_latitud = Column(Float, nullable=True)
    ubicacion_longitud = Column(Float, nullable=True)
    ultima_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con asignaciones
    asignaciones = relationship("Asignacion", back_populates="conductor")
    
    def __repr__(self):
        return f"<Conductor {self.id_conductor} - {self.estado.value}>"


class Asignacion(Base):
    """Tabla: asignaciones"""
    __tablename__ = "asignaciones"
    
    id_asignacion = Column(Integer, primary_key=True, autoincrement=True, index=True)
    id_viaje = Column(Integer, nullable=False, index=True)
    id_conductor = Column(Integer, ForeignKey("disponibilidad_conductores.id_conductor"), nullable=False)
    fecha_asignacion = Column(DateTime, default=datetime.utcnow)
    prioridad = Column(SQLEnum(PrioridadAsignacion), default=PrioridadAsignacion.MEDIA)
    algoritmo_usado = Column(String(50), nullable=True)  # ej: "cercania", "turno", "prioridad"
    
    # Relación con conductor
    conductor = relationship("DisponibilidadConductor", back_populates="asignaciones")
    
    def __repr__(self):
        return f"<Asignacion {self.id_asignacion} - Viaje:{self.id_viaje} Conductor:{self.id_conductor}>"


# Función para obtener sesión de BD
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Crear todas las tablas
def create_tables():
    Base.metadata.create_all(bind=engine)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.models.database import get_db, DisponibilidadConductor, Asignacion, EstadoConductor
from app.schemas.schemas import (
    ConductorCreate, ConductorResponse, ConductorUpdate,
    AsignacionResponse, SolicitudViajeEvent
)
from app.services.asignacion_service import AsignacionService

router = APIRouter()


# ========== ENDPOINTS DE CONDUCTORES ==========

@router.post("/conductores/", response_model=ConductorResponse, status_code=status.HTTP_201_CREATED)
def crear_conductor(conductor: ConductorCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo conductor en el sistema de despacho
    """
    # Verificar si el conductor ya existe
    db_conductor = db.query(DisponibilidadConductor).filter(
        DisponibilidadConductor.id_conductor == conductor.id_conductor
    ).first()
    
    if db_conductor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El conductor {conductor.id_conductor} ya está registrado"
        )
    
    nuevo_conductor = DisponibilidadConductor(
        id_conductor=conductor.id_conductor,
        estado=EstadoConductor.DISPONIBLE,
        ubicacion_latitud=conductor.ubicacion_latitud,
        ubicacion_longitud=conductor.ubicacion_longitud
    )
    
    db.add(nuevo_conductor)
    db.commit()
    db.refresh(nuevo_conductor)
    
    return nuevo_conductor


@router.get("/conductores/", response_model=List[ConductorResponse])
def listar_conductores(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Lista todos los conductores registrados
    """
    conductores = db.query(DisponibilidadConductor).offset(skip).limit(limit).all()
    return conductores


@router.get("/conductores/{id_conductor}", response_model=ConductorResponse)
def obtener_conductor(id_conductor: int, db: Session = Depends(get_db)):
    """
    Obtiene la información de un conductor específico
    """
    conductor = db.query(DisponibilidadConductor).filter(
        DisponibilidadConductor.id_conductor == id_conductor
    ).first()
    
    if not conductor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conductor {id_conductor} no encontrado"
        )
    
    return conductor


@router.patch("/conductores/{id_conductor}", response_model=ConductorResponse)
def actualizar_conductor(
    id_conductor: int,
    conductor_update: ConductorUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza el estado o ubicación de un conductor
    """
    conductor = db.query(DisponibilidadConductor).filter(
        DisponibilidadConductor.id_conductor == id_conductor
    ).first()
    
    if not conductor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conductor {id_conductor} no encontrado"
        )
    
    # Actualizar campos
    if conductor_update.estado:
        conductor.estado = EstadoConductor[conductor_update.estado.value.upper()]
    if conductor_update.ubicacion_latitud is not None:
        conductor.ubicacion_latitud = conductor_update.ubicacion_latitud
    if conductor_update.ubicacion_longitud is not None:
        conductor.ubicacion_longitud = conductor_update.ubicacion_longitud
    
    db.commit()
    db.refresh(conductor)
    
    return conductor


@router.get("/conductores/disponibles/listar", response_model=List[ConductorResponse])
def listar_conductores_disponibles(db: Session = Depends(get_db)):
    """
    Lista solo los conductores disponibles
    """
    conductores = AsignacionService.obtener_conductores_disponibles(db)
    return conductores


# ========== ENDPOINTS DE ASIGNACIONES ==========

@router.get("/asignaciones/", response_model=List[AsignacionResponse])
def listar_asignaciones(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Lista todas las asignaciones realizadas
    """
    asignaciones = db.query(Asignacion).offset(skip).limit(limit).all()
    return asignaciones


@router.get("/asignaciones/{id_asignacion}", response_model=AsignacionResponse)
def obtener_asignacion(id_asignacion: int, db: Session = Depends(get_db)):
    """
    Obtiene una asignación específica
    """
    asignacion = db.query(Asignacion).filter(
        Asignacion.id_asignacion == id_asignacion
    ).first()
    
    if not asignacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asignación {id_asignacion} no encontrada"
        )
    
    return asignacion


@router.get("/asignaciones/viaje/{id_viaje}", response_model=AsignacionResponse)
def obtener_asignacion_por_viaje(id_viaje: int, db: Session = Depends(get_db)):
    """
    Obtiene la asignación de un viaje específico
    """
    asignacion = db.query(Asignacion).filter(
        Asignacion.id_viaje == id_viaje
    ).first()
    
    if not asignacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró asignación para el viaje {id_viaje}"
        )
    
    return asignacion


@router.post("/asignaciones/liberar-conductor/{id_conductor}")
def liberar_conductor(id_conductor: int, db: Session = Depends(get_db)):
    """
    Libera un conductor (lo marca como disponible)
    """
    resultado = AsignacionService.liberar_conductor(db, id_conductor)
    
    if resultado:
        return {"mensaje": f"Conductor {id_conductor} liberado exitosamente"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conductor {id_conductor} no encontrado"
        )


# ========== ENDPOINT DE HEALTH CHECK ==========

@router.get("/health")
def health_check():
    """
    Endpoint de verificación de salud del servicio
    """
    return {
        "status": "healthy",
        "service": "servicio-despacho",
        "version": "1.0.0"
    }
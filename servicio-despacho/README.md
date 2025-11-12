# 🚖 Servicio de Despacho - SmartRide

Microservicio de asignación de conductores desarrollado en Python con FastAPI y gRPC.

## 📋 Descripción

Este servicio es responsable de:
- Recibir solicitudes de viajes desde RabbitMQ
- Asignar conductores disponibles usando algoritmos de cercanía
- Comunicarse con el servicio de reservas mediante gRPC
- Gestionar la disponibilidad de conductores en tiempo real

## 🏗️ Arquitectura

- **Framework**: FastAPI (REST API)
- **Comunicación**: gRPC + RabbitMQ
- **Base de datos**: PostgreSQL
- **Lenguaje**: Python 3.11

## 📁 Estructura del Proyecto

```
servicio-despacho/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Aplicación FastAPI principal
│   ├── config.py                  # Configuración
│   ├── api/
│   │   └── routes.py              # Endpoints REST
│   ├── grpc_service/
│   │   ├── server.py              # Servidor gRPC
│   │   ├── client.py              # Cliente gRPC
│   │   └── protos/
│   │       └── despacho.proto     # Definición gRPC
│   ├── messaging/
│   │   ├── rabbitmq_consumer.py   # Consumidor RabbitMQ
│   │   └── rabbitmq_publisher.py  # Publicador RabbitMQ
│   ├── services/
│   │   └── asignacion_service.py  # Lógica de asignación
│   ├── models/
│   │   └── database.py            # Modelos SQLAlchemy
│   └── schemas/
│       └── schemas.py             # Schemas Pydantic
├── .env                           # Variables de entorno
├── requirements.txt               # Dependencias
├── Dockerfile                     # Imagen Docker
└── docker-compose.yml             # Orquestación
```

## 🚀 Instalación y Ejecución

### Prerrequisitos

- Python 3.11+
- PostgreSQL
- RabbitMQ
- Docker y Docker Compose (opcional)

### Opción 1: Ejecución Local

#### Paso 1: Clonar y configurar el entorno

```bash
# Crear directorio del proyecto
mkdir servicio-despacho
cd servicio-despacho

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate
```

#### Paso 2: Instalar dependencias

```bash
pip install -r requirements.txt
```

#### Paso 3: Configurar variables de entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env con tus configuraciones
nano .env  # o usa tu editor preferido
```

#### Paso 4: Generar archivos protobuf de gRPC

```bash
python -m grpc_tools.protoc \
    -I./app/grpc_service/protos \
    --python_out=./app/grpc_service/protos \
    --grpc_python_out=./app/grpc_service/protos \
    ./app/grpc_service/protos/despacho.proto
```

#### Paso 5: Configurar PostgreSQL

```bash
# Crear base de datos
psql -U postgres
CREATE DATABASE despacho_db;
CREATE USER despacho_user WITH PASSWORD 'despacho_pass';
GRANT ALL PRIVILEGES ON DATABASE despacho_db TO despacho_user;
\q
```

#### Paso 6: Ejecutar el servicio

```bash
# Opción 1: Con uvicorn directamente
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload

# Opción 2: Con python
python -m app.main
```

### Opción 2: Ejecución con Docker

#### Paso 1: Construir y ejecutar con Docker Compose

```bash
# Construir imágenes
docker-compose build

# Iniciar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f servicio-despacho
```

#### Paso 2: Verificar que los servicios están corriendo

```bash
# Ver estado de los contenedores
docker-compose ps

# Verificar salud del servicio
curl http://localhost:8003/api/v1/health
```

## 📡 Endpoints API REST

### Health Check
```
GET /api/v1/health
```

### Conductores

```
POST   /api/v1/conductores/                    # Crear conductor
GET    /api/v1/conductores/                    # Listar conductores
GET    /api/v1/conductores/{id}                # Obtener conductor
PATCH  /api/v1/conductores/{id}                # Actualizar conductor
GET    /api/v1/conductores/disponibles/listar  # Listar disponibles
```

### Asignaciones

```
GET    /api/v1/asignaciones/                   # Listar asignaciones
GET    /api/v1/asignaciones/{id}               # Obtener asignación
GET    /api/v1/asignaciones/viaje/{id_viaje}   # Asignación por viaje
POST   /api/v1/asignaciones/liberar-conductor/{id} # Liberar conductor
```

## 🔌 Servicios gRPC

### Métodos disponibles:

1. **AsignarConductor**: Asigna un conductor a un viaje
2. **ObtenerEstadoConductor**: Consulta estado de un conductor
3. **ActualizarDisponibilidad**: Actualiza ubicación/estado

### Ejemplo de uso con grpcurl:

```bash
# Listar servicios
grpcurl -plaintext localhost:50051 list

# Llamar a AsignarConductor
grpcurl -plaintext -d '{
  "id_viaje": 1,
  "id_cliente": 100,
  "origen_lat": -16.5000,
  "origen_lon": -68.1500,
  "destino_lat": -16.5200,
  "destino_lon": -68.1300,
  "prioridad": "alta"
}' localhost:50051 despacho.DespachoService/AsignarConductor
```

## 📨 Integración con RabbitMQ

### Colas consumidas:
- `nuevas_reservas`: Escucha nuevas solicitudes de viajes

### Colas publicadas:
- `asignaciones_completadas`: Publica asignaciones exitosas

### Ejemplo de mensaje consumido:

```json
{
  "id_viaje": 123,
  "id_cliente": 456,
  "punto_origen_lat": -16.5000,
  "punto_origen_lon": -68.1500,
  "punto_destino_lat": -16.5200,
  "punto_destino_lon": -68.1300,
  "prioridad": "media"
}
```

## 🧪 Pruebas

### Ejecutar tests

```bash
# Instalar dependencias de test
pip install pytest pytest-asyncio pytest-cov

# Ejecutar tests
pytest

# Con cobertura
pytest --cov=app tests/
```

### Probar manualmente con curl

```bash
# Crear conductor
curl -X POST http://localhost:8003/api/v1/conductores/ \
  -H "Content-Type: application/json" \
  -d '{
    "id_conductor": 1,
    "ubicacion_latitud": -16.5000,
    "ubicacion_longitud": -68.1500
  }'

# Listar conductores disponibles
curl http://localhost:8003/api/v1/conductores/disponibles/listar
```

## 📊 Documentación API

Una vez ejecutando el servicio, accede a:

- **Swagger UI**: http://localhost:8003/docs
- **ReDoc**: http://localhost:8003/redoc

## 🛠️ Algoritmo de Asignación

El servicio utiliza el **algoritmo de cercanía** por defecto:

1. Recibe solicitud de viaje con origen
2. Consulta conductores con estado "DISPONIBLE"
3. Calcula distancia usando fórmula de Haversine
4. Selecciona el conductor más cercano
5. Crea asignación y marca conductor como "OCUPADO"
6. Publica evento a RabbitMQ

## 🔄 Manejo de Concurrencia

- **Transacciones atómicas** en PostgreSQL
- **QoS de RabbitMQ** (prefetch_count=1)
- **Bloqueo optimista** en actualización de estados
- **Reintento automático** si no hay conductores disponibles

## 📈 Monitoreo

### Logs

```bash
# Ver logs en tiempo real
docker-compose logs -f servicio-despacho

# Logs de RabbitMQ
docker-compose logs -f rabbitmq
```

### RabbitMQ Management UI

Accede a http://localhost:15672
- Usuario: `guest`
- Contraseña: `guest`

## 🐛 Troubleshooting

### Error de conexión a PostgreSQL

```bash
# Verificar que PostgreSQL esté corriendo
docker-compose ps postgres-despacho

# Ver logs de PostgreSQL
docker-compose logs postgres-despacho
```

### Error generando archivos protobuf

```bash
# Instalar grpcio-tools
pip install grpcio-tools

# Regenerar archivos
python -m grpc_tools.protoc -I./app/grpc_service/protos --python_out=./app/grpc_service/protos --grpc_python_out=./app/grpc_service/protos ./app/grpc_service/protos/despacho.proto
```

### RabbitMQ no conecta

```bash
# Verificar estado de RabbitMQ
docker-compose ps rabbitmq

# Reiniciar RabbitMQ
docker-compose restart rabbitmq
```

## 📝 Variables de Entorno

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| PORT | Puerto FastAPI | 8003 |
| GRPC_PORT | Puerto gRPC | 50051 |
| DATABASE_URL | URL de PostgreSQL | postgresql://... |
| RABBITMQ_HOST | Host de RabbitMQ | localhost |
| LOG_LEVEL | Nivel de logs | INFO |

## 🤝 Integración con otros microservicios

Este servicio se integra con:

- **Servicio de Reservas** (Node.js): Vía gRPC y RabbitMQ
- **Servicio de Notificaciones** (Java): Vía RabbitMQ
- **Servicio de Usuarios** (NestJS): Consulta datos de conductores

## 📄 Licencia

Proyecto académico - SmartRide System

## 👥 Autor

Desarrollado para el proyecto de Sistemas Distribuidos - Microservicios
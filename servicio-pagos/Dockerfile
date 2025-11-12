# Usamos la imagen oficial de Rust con Alpine
FROM rust:1.65-alpine as builder

# Instalamos las dependencias necesarias (como SSL)
RUN apk add --no-cache libssl3

# Directorio de trabajo en el contenedor
WORKDIR /app

# Copiar los archivos de configuración y dependencias
COPY Cargo.toml Cargo.lock ./

# Instalar dependencias de Rust
RUN cargo fetch

# Copiar todo el código fuente
COPY . .

# Construir el proyecto en modo release
RUN cargo build --release

# Imagen final
FROM alpine:latest

# Instalamos las dependencias necesarias para la ejecución
RUN apk add --no-cache libssl3

# Copiamos el binario desde el contenedor de construcción
COPY --from=builder /app/target/release/servicio-pagos /usr/local/bin/

# Exponer el puerto 8080
EXPOSE 8080

# Comando para ejecutar el servicio
CMD ["servicio-pagos"]

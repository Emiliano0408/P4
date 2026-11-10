# Usar una imagen oficial de Python ligera
FROM python:3.11-slim

# Instalar dependencias del sistema necesarias para tkinter
RUN apt-get update && apt-get install -y \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el código fuente al contenedor
COPY src/ /app/src/

# Comando por defecto para ejecutar la aplicación
CMD ["python", "src/app.py"]
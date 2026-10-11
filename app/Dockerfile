# Imagen base: Python ya instalado
FROM python:3.12-slim

# Carpeta de trabajo dentro del contenedor
WORKDIR /app

# Primero solo las dependencias, para aprovechar la caché de capas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Después, el resto del código
COPY . .

CMD ["streamlit", "run", "main.py", \
     "--server.address=0.0.0.0", "--server.port=8501", \
     "--server.headless=true", "--browser.gatherUsageStats=false"]
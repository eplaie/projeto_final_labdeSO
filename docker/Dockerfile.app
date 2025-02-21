FROM python:3.9-slim

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia os requisitos e instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação E os templates
COPY src/image_processor.py .
COPY src/api.py .
COPY src/templates ./templates

# Expõe a porta da API
EXPOSE 5000

# Comando para iniciar a aplicação
CMD ["python", "api.py"]
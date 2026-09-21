# ==========================================
# Dockerfile para o módulo RPA LMS (LG Electronics)
# ==========================================

# Imagem base oficial do Python slim para menor footprint e máxima performance
FROM python:3.11-slim

# Metadados e variáveis de ambiente para otimização do runtime Python e Playwright
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    HEADLESS=true

# Diretório de trabalho dentro do contêiner
WORKDIR /app

# Instalação de bibliotecas do sistema essenciais para OpenCV, ONNX Runtime e certificados
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copia os requisitos e instala dependências Python e o navegador Chromium com suas dependências de SO
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    playwright install --with-deps chromium

# Copia todo o código-fonte do RPA para dentro do contêiner
COPY . .

# Comando padrão de execução do contêiner (pode ser sobrescrito pelo compose ou CLI)
CMD ["python", "login.py"]

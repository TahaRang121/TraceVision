FROM python:3.10-slim

WORKDIR /workspace

# Install system dependencies for OpenCV and networking
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU first for speed and compactness
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Copy requirements and install
COPY backend/requirements.txt /workspace/backend/requirements.txt
RUN pip install --no-cache-dir -r /workspace/backend/requirements.txt
RUN pip install --no-cache-dir yacs gdown loguru thop scipy

# Copy codebase
COPY . /workspace/

ENV PYTHONPATH="/workspace:/workspace/backend:/workspace/ai-engine:/workspace/person-tracking/third_party/ByteTrack"
ENV DATABASE_URL="postgresql+asyncpg://postgres:postgrespassword@postgres:5432/tracevision"
ENV QDRANT_HOST="qdrant"
ENV QDRANT_PORT="6333"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--app-dir", "/workspace/backend", "--host", "0.0.0.0", "--port", "8000"]


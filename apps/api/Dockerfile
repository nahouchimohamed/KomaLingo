FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    fonts-noto-core \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-ocr.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && (pip install --no-cache-dir -r requirements-ocr.txt || echo "PaddleOCR install failed; stub OCR will be used")

COPY . .

RUN mkdir -p /app/data/uploads /app/data/results /app/fonts \  # runtime storage
    && (cp /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf /app/fonts/NotoSans-Regular.ttf || true) \
    && (cp /usr/share/fonts/truetype/noto/NotoSans-Regular.ttf /app/fonts/NotoSans-Regular.ttf || true)

ENV PYTHONPATH=/app
ENV DATA_DIR=/app/data
ENV HOME=/tmp

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

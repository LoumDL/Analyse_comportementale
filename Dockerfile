FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY modele_AI/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY modele_AI/api.py .
COPY modele_AI/process/ ./process/
COPY modele_AI/yolo26n.pt .
COPY modele_AI/site_config.json .

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]

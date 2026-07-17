FROM node:22-alpine AS executive-kpi-builder

WORKDIR /app/frontend/executive-kpi

COPY frontend/executive-kpi/package.json frontend/executive-kpi/package-lock.json ./
RUN npm ci

COPY frontend/executive-kpi/ ./
RUN npm run build


FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=executive-kpi-builder /app/src/app/static/build/executive-kpi ./src/app/static/build/executive-kpi

EXPOSE 8000

CMD ["python", "run_api.py", "--host", "0.0.0.0", "--port", "8000"]

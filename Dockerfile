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
COPY deploy/verify_cpu_only_torch.py deploy/verify_cpu_only_torch.py

# Production is a CPU-only host with no CUDA/GPU workload. The default PyPI
# torch wheel declares nvidia-cudnn-cu13, nvidia-cusparselt-cu13,
# nvidia-nccl-cu13, nvidia-nvshmem-cu13 and triton under
# `platform_system == "Linux"`, which added several GB to the image and
# exhausted the disk while unpacking libcusparseLt.so.0. Install the exact CPU
# build from PyTorch's official CPU index FIRST; the requirements resolution
# below then finds torch>=2.2 already satisfied and leaves it in place.
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu \
        torch==2.14.0+cpu \
    && pip install --no-cache-dir -r requirements.txt \
    && python deploy/verify_cpu_only_torch.py

COPY . .
COPY --from=executive-kpi-builder /app/src/app/static/build/executive-kpi ./src/app/static/build/executive-kpi

# Git and Docker COPY do not normalize group-writable host modes. Keep the
# packaged routing authority and only its required parent directories within
# the production loader's immutable-file permission boundary.
RUN chmod 0755 /app/src /app/src/evaluation \
    && chmod 0644 \
        /app/src/evaluation/production_provider_qualification_registry_v1.json \
        /app/src/evaluation/renderer_bound_v2_skill_qualification_registry.json \
        /app/src/evaluation/renderer_bound_v2_job_fit_qualification_registry.json

EXPOSE 8000

CMD ["python", "run_api.py", "--host", "0.0.0.0", "--port", "8000"]

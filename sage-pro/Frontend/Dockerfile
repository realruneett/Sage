# SAGE-PRO Deployment Image for AMD MI300X (ROCm)
FROM rocm/pytorch:rocm6.2_ubuntu22.04_py3.10_pytorch_release_2.3.1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y \
    git curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements-core.txt .
RUN pip install --no-cache-dir -r requirements-core.txt

# Copy SAGE-PRO source
COPY sage-pro/ ./sage-pro/
COPY app.py .

# Environment
ENV SAGE_MODE=pro
ENV PYTHONPATH=/app/sage-pro:$PYTHONPATH
ENV ROCM_VISIBLE_DEVICES=0,1,2,3,4,5,6,7
ENV HSA_OVERRIDE_GFX_VERSION=9.4.2

EXPOSE 7860

CMD ["python", "app.py"]

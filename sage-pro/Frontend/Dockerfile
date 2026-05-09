# SAGE-PRO Frontend — Lightweight Gradio container
# Runs independently from the backend; connects via SAGE_BACKEND_URL

FROM python:3.11-slim

WORKDIR /app

# Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app.py .
COPY README.md .

# Gradio needs this for HF Spaces compatibility
ENV GRADIO_SERVER_NAME=0.0.0.0
ENV GRADIO_SERVER_PORT=7860

EXPOSE 7860

CMD ["python", "app.py"]

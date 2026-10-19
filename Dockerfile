FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" python-multipart
COPY . .
EXPOSE 8100
# Text mode by default; build with the full requirements to enable Whisper STT.
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8100"]

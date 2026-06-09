FROM python:3.12-slim AS backend

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/src ./src

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.14-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 100 app:app
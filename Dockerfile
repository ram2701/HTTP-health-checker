FROM python:3.13-alpine

WORKDIR /app

RUN apk add --no-cache \
    gcc \
    libpq-dev \
    py3-gobject3 \
    python3-dev \
    py3-pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DATABASE_URL=postgresql://postgres:postgres@db:5432/health
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
ENV OTEL_EXPORTER_OTLP_PROTOCOL=grpc
ENV OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true

CMD ["opentelemetry-instrument", "--service_name", "healthcheck", "flask", "--app", "run.py", "run", "--host", "0.0.0.0"]

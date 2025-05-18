from flask import Flask
from .views import bp
from .scheduler import start_scheduler
from .models import Base
from .database import engine

from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace.export import ConsoleSpanExporter

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

trace.set_tracer_provider(
    TracerProvider(
        resource=Resource.create({SERVICE_NAME: "healthcheck-service"})
    )
)

# Exportador a Jaeger (por defecto en localhost:6831)
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",  # nombre del contenedor si estás en Docker
    agent_port=6831,
)

trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)


app = Flask(__name__)

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Registrar rutas
app.register_blueprint(bp)

# Iniciar tareas periódicas
start_scheduler()
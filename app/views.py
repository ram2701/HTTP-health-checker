from flask import Blueprint, request, jsonify, abort
from .models import Service, HealthCheck
from .database import SessionLocal

from opentelemetry import metrics, trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter


bp = Blueprint("api", __name__)

tracer = trace.get_tracer("create-service.tracer")

meter = metrics.get_meter("healthcheck.meter")

request_count = meter.create_gauge("healthcheck.request_counter")
request_counter = meter.create_counter("healthcheck.counter")

@bp.route("/services", methods=["POST"])
def add_service():
    
    with tracer.start_as_current_span("creation_of_petition_trace") as span_petition:
        try:
            data = request.get_json(silent=True)
            if not data or "name" not in data or "url" not in data:
                return {"error": "Not valid JSON. Expected: {name, url}"}, 400

            session = SessionLocal()
            try:
                service = Service(name=data["name"], url=data["url"])
                session.add(service)
                session.flush()            
                service_id = service.id    
                session.commit()

                request_counter.add(1)

                span_petition.add_event("Peticion creada correctamente")
                span_petition.set_attributes({
                    "task.name": data["name"],
                    "task.url": data["url"]
                })
    			
                span_petition.set_status(Status(StatusCode.OK))


                return {"id": service_id, "status": "registered"}, 201
            except Exception as e:
                session.rollback()
                return {"error": str(e)}, 500
            finally:
                session.close()
        except Exception as ex:
	
            span_petition.set_status(Status(StatusCode.ERROR))
            span_petition.record_exception(ex)


@bp.route("/services", methods=["GET"])
def list_services():
    session = SessionLocal()
    services = session.query(Service).all()
    result = []
    request_count.set(len(services))
    for service in services:
        last_check = (
            session.query(HealthCheck)
            .filter_by(service_id=service.id)
            .order_by(HealthCheck.timestamp.desc())
            .first()
        )
        result.append({
            "id": service.id,
            "name": service.name,
            "url": service.url,
            "last_status": last_check.status_code if last_check else None,
            "latency_ms": last_check.response_time_ms if last_check else None,
            "last_checked": last_check.timestamp.isoformat() if last_check else None
        })
    session.close()
    return jsonify(result)

@bp.route("/bad")
def bad():
    abort(400)

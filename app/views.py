from flask import Blueprint, request, jsonify
from .models import Service, HealthCheck
from .database import SessionLocal

from opentelemetry import metrics

bp = Blueprint("api", __name__)

meter = metrics.get_meter("" \
"healthcheck.meter")

request_count = meter.create_gauge("healthcheck.request_counter")

@bp.route("/services", methods=["POST"])
def add_service():
    data = request.get_json(silent=True)
    if not data or "name" not in data or "url" not in data:
        return {"error": "JSON inválido. Esperado: {name, url}"}, 400

    session = SessionLocal()
    try:
        service = Service(name=data["name"], url=data["url"])
        session.add(service)
        session.flush()            
        service_id = service.id    
        session.commit()



        return {"id": service_id, "status": "registered"}, 201
    except Exception as e:
        session.rollback()
        return {"error": str(e)}, 500
    finally:
        session.close()

@bp.route("/services", methods=["GET"])
def list_services():
    session = SessionLocal()
    services = session.query(Service).all()
    result = []
    request_count.set(services.count())
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

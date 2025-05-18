from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import requests
from .models import Service, HealthCheck
from .database import SessionLocal

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode


tracer = trace.get_tracer("healthcheck.tracer")

def check_service(service):
    
    with tracer.start_as_current_span("healthcheck") as span_healthcheck:
        
        try:
          
            session = SessionLocal()
            try:
                start = datetime.now()
                response = requests.get(service.url, timeout=5)
                duration = (datetime.now() - start).total_seconds() * 1000
                health = HealthCheck(
                    service_id=service.id,
                    status_code=response.status_code,
                    response_time_ms=duration,
                )
                if response.status_code == 200:
                    span_healthcheck.set_status(Status(StatusCode.OK))
                else:
                    span_healthcheck.set_status(Status(StatusCode.ERROR))

            except requests.RequestException as e:
                health = HealthCheck(
                    service_id=service.id,
                    status_code=503,
                    response_time_ms=None,
                    error=str(e),
                )
                span_healthcheck.set_status(Status(StatusCode.ERROR))

            session.add(health)
            session.commit()
            session.close()
        except Exception as ex:

            span_healthcheck.set_status(Status(StatusCode.ERROR))
            span_healthcheck.record_exception(ex)

def run_checks():
    session = SessionLocal()
    services = session.query(Service).all()
    session.close()
    for service in services:
        check_service(service)

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_checks, "interval", seconds=60)
    scheduler.start()
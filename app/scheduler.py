import logging
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import requests
from sqlalchemy import asc
from .models import Service, HealthCheck
from .database import SessionLocal

from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode

meter = metrics.get_meter("scheduler.meter")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

tracer = trace.get_tracer("healthcheck.tracer")

good_request = meter.create_gauge("good_request_gauge")
bad_request = meter.create_gauge("bad_request_gauge")



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
                    logger.warning(f"The page {service.name} has returned a 200")
                else:
                    span_healthcheck.set_status(Status(StatusCode.ERROR))
                    logger.warning(f"The page {service.name} has returned a {response.status_code}")


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

def count_urls():
    session = SessionLocal()
    services = session.query(Service).all()
    good_counter = 0
    bad_counter = 0

    for service in services:
        try:
            response = requests.get(service.url, timeout=2)
            if response.status_code == 200:
                good_counter += 1
            else:
                bad_counter += 1

        except requests.RequestException:
            continue
    session.close()
    good_request.set(good_counter)
    bad_request.set(bad_counter)


def run_checks():
    session = SessionLocal()
    services = session.query(Service).all()
    session.close()
    for service in services:
        check_service(service)
    count_urls()

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_checks, "interval", seconds=60)
    scheduler.start()
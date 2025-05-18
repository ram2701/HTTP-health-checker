from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Service(Base):
    __tablename__ = "service"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    url = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    checks = relationship("HealthCheck", back_populates="service")

class HealthCheck(Base):
    __tablename__ = "health_check"
    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey("service.id"), nullable=False)
    status_code = Column(Integer)
    response_time_ms = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    error = Column(String(500), nullable=True)
    service = relationship("Service", back_populates="checks")
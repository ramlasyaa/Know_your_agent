import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AgentAction(Base):
    """Represents a proposed action by an autonomous AI agent."""
    __tablename__ = "agent_actions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    agent_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    action_type = Column(String(50), nullable=False)  # e.g., 'payment', 'order_checkout', 'subscription'
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    merchant_name = Column(String(150), nullable=False)
    is_new_merchant = Column(Boolean, default=False, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    device_id = Column(String(100), nullable=True)
    metadata_json = Column(JSON, nullable=True)

    # Relationships
    risk_score = relationship("RiskScore", back_populates="action", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="action", cascade="all, delete-orphan")


class RiskScore(Base):
    """Stores the fraud risk scoring and SHAP explanation for an agent action."""
    __tablename__ = "risk_scores"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    action_id = Column(String(36), ForeignKey("agent_actions.id", ondelete="CASCADE"), nullable=False, unique=True)
    risk_score = Column(Float, nullable=False)  # 0.0 to 100.0
    flagged = Column(Boolean, nullable=False, index=True)
    risk_level = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    rule_flags = Column(JSON, nullable=False, default=list)  # List of triggered rules
    ml_anomaly_score = Column(Float, nullable=False, default=0.0)  # Raw ML score
    shap_explanation = Column(JSON, nullable=False, default=dict)  # Feature attributions & human text
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    action = relationship("AgentAction", back_populates="risk_score")


class AuditLog(Base):
    """Immutable audit log recording all evaluation events and human actions."""
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    action_id = Column(String(36), ForeignKey("agent_actions.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # ACTION_SCORED, FLAGGED, OVERRIDDEN, APPROVED
    performed_by = Column(String(100), nullable=False, default="KYA_RISK_ENGINE")
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    details = Column(JSON, nullable=False, default=dict)

    # Relationships
    action = relationship("AgentAction", back_populates="audit_logs")

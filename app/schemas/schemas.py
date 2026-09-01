from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class AgentActionCreate(BaseModel):
    agent_id: str = Field(..., json_schema_extra={"example": "agent_shopping_01"}, description="Identifier of the autonomous agent")
    user_id: str = Field(..., json_schema_extra={"example": "usr_98765"}, description="User on whose behalf action is taken")
    action_type: str = Field(..., json_schema_extra={"example": "payment"}, description="Type: payment, order_checkout, subscription")
    amount: float = Field(..., gt=0, json_schema_extra={"example": 450.00}, description="Monetary value of transaction")
    currency: str = Field(default="USD", json_schema_extra={"example": "USD"})
    merchant_name: str = Field(..., json_schema_extra={"example": "Acme Tech Store"}, description="Target merchant or payee")
    is_new_merchant: bool = Field(default=False, description="True if agent has never interacted with merchant")
    timestamp: Optional[datetime] = Field(default=None, description="Action timestamp, defaults to now if omitted")
    ip_address: Optional[str] = Field(default=None, json_schema_extra={"example": "192.168.1.50"})
    device_id: Optional[str] = Field(default=None, json_schema_extra={"example": "device_macbook_pro"})
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom agent metadata")


class AgentActionResponse(BaseModel):
    id: str
    agent_id: str
    user_id: str
    action_type: str
    amount: float
    currency: str
    merchant_name: str
    is_new_merchant: bool
    timestamp: datetime
    ip_address: Optional[str] = None
    device_id: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class RuleFlagDetail(BaseModel):
    rule_name: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    points: float
    description: str


class ShapFeatureImpact(BaseModel):
    feature: str
    feature_value: Any
    shap_value: float
    contribution_pts: float
    impact_description: str


class ShapExplanationDetail(BaseModel):
    base_score: float
    shap_values: Dict[str, float]
    feature_impacts: List[ShapFeatureImpact]
    summary_reasons: List[str]


class RiskScoreResponse(BaseModel):
    id: str
    action_id: str
    risk_score: float = Field(..., description="Combined risk score from 0.0 to 100.0")
    flagged: bool = Field(..., description="True if action is flagged for human review/override")
    risk_level: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    rule_flags: List[RuleFlagDetail]
    ml_anomaly_score: float
    shap_explanation: ShapExplanationDetail
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScoreActionResponse(BaseModel):
    action: AgentActionResponse
    risk_score: RiskScoreResponse
    recommendation: str  # 'ALLOW' or 'FLAG_FOR_HUMAN_REVIEW'
    decision_reason: str


class AuditLogResponse(BaseModel):
    id: str
    action_id: str
    event_type: str
    performed_by: str
    timestamp: datetime
    details: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class ActionDetailWithScore(BaseModel):
    action: AgentActionResponse
    risk_score: Optional[RiskScoreResponse] = None


class StatsResponse(BaseModel):
    total_actions: int
    flagged_actions: int
    clean_actions: int
    flag_rate_percentage: float
    average_risk_score: float
    high_risk_actions: int

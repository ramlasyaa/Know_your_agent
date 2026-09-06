import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.models import AgentAction, RiskScore, AuditLog
from app.schemas.schemas import (
    AgentActionCreate,
    AgentActionResponse,
    RiskScoreResponse,
    ScoreActionResponse,
    AuditLogResponse,
    ActionDetailWithScore,
    StatsResponse
)
from app.scoring.engine import HybridRiskEngine

from fastapi.responses import RedirectResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Global Singleton Risk Engine instance
risk_engine = HybridRiskEngine()


@router.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect root path to interactive OpenAPI /docs UI."""
    return RedirectResponse(url="/docs")


@router.post(
    "/score-action",
    response_model=ScoreActionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Score an agent action for trust & fraud risk"
)
async def score_action(
    payload: AgentActionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Evaluates a proposed AI agent action against velocity limits, explicit hard rules,
    and Isolation Forest ML anomaly detection, returning a risk score (0-100), boolean flag,
    and detailed SHAP explainability feature attributions.
    """
    timestamp = payload.timestamp or datetime.now(timezone.utc)

    # 1. Calculate Velocity metrics from Database
    window_5m_start = timestamp - timedelta(minutes=5)
    window_1h_start = timestamp - timedelta(hours=1)

    # Count actions by this agent in last 5 minutes
    stmt_5m = select(func.count(AgentAction.id)).where(
        AgentAction.agent_id == payload.agent_id,
        AgentAction.timestamp >= window_5m_start
    )
    res_5m = await db.execute(stmt_5m)
    velocity_5m = res_5m.scalar() or 0

    # Count actions by this agent in last 1 hour
    stmt_1h = select(func.count(AgentAction.id)).where(
        AgentAction.agent_id == payload.agent_id,
        AgentAction.timestamp >= window_1h_start
    )
    res_1h = await db.execute(stmt_1h)
    velocity_1h = res_1h.scalar() or 0

    # Calculate average transaction amount for this user
    stmt_avg = select(func.avg(AgentAction.amount)).where(
        AgentAction.user_id == payload.user_id
    )
    res_avg = await db.execute(stmt_avg)
    avg_user_amount = res_avg.scalar() or 50.0

    # 2. Evaluate with Hybrid Risk Engine
    eval_result = risk_engine.evaluate_action(
        action_type=payload.action_type,
        amount=payload.amount,
        is_new_merchant=payload.is_new_merchant,
        merchant_name=payload.merchant_name,
        timestamp=timestamp,
        recent_actions_count_5m=velocity_5m,
        recent_actions_count_1h=velocity_1h,
        avg_user_amount=float(avg_user_amount)
    )

    # 3. Create AgentAction Record
    db_action = AgentAction(
        agent_id=payload.agent_id,
        user_id=payload.user_id,
        action_type=payload.action_type,
        amount=payload.amount,
        currency=payload.currency,
        merchant_name=payload.merchant_name,
        is_new_merchant=payload.is_new_merchant,
        timestamp=timestamp,
        ip_address=payload.ip_address,
        device_id=payload.device_id,
        metadata_json=payload.metadata
    )
    db.add(db_action)
    await db.flush()  # populate db_action.id

    # 4. Create RiskScore Record
    db_risk_score = RiskScore(
        action_id=db_action.id,
        risk_score=eval_result["risk_score"],
        flagged=eval_result["flagged"],
        risk_level=eval_result["risk_level"],
        rule_flags=eval_result["rule_flags"],
        ml_anomaly_score=eval_result["ml_anomaly_score"],
        shap_explanation=eval_result["shap_explanation"]
    )
    db.add(db_risk_score)

    # 5. Create Audit Log Entry
    audit_event = "FLAGGED_HUMAN_REVIEW" if eval_result["flagged"] else "ACTION_APPROVED"
    db_audit = AuditLog(
        action_id=db_action.id,
        event_type=audit_event,
        performed_by="KYA_HYBRID_ENGINE",
        details={
            "score": float(eval_result["risk_score"]),
            "risk_level": str(eval_result["risk_level"]),
            "flagged": bool(eval_result["flagged"]),
            "decision_reason": str(eval_result["decision_reason"])
        }
    )
    db.add(db_audit)
    await db.commit()

    # Refresh models for response building
    await db.refresh(db_action)
    await db.refresh(db_risk_score)

    return ScoreActionResponse(
        action=AgentActionResponse.model_validate(db_action),
        risk_score=RiskScoreResponse.model_validate(db_risk_score),
        recommendation=eval_result["recommendation"],
        decision_reason=eval_result["decision_reason"]
    )


@router.get(
    "/actions",
    response_model=List[ActionDetailWithScore],
    summary="Get recent agent actions with risk scores"
)
async def list_actions(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    flagged_only: bool = Query(default=False),
    agent_id: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves recent agent actions with their computed risk scores and SHAP explanations."""
    stmt = (
        select(AgentAction)
        .options(selectinload(AgentAction.risk_score))
        .order_by(desc(AgentAction.timestamp))
    )

    if agent_id:
        stmt = stmt.where(AgentAction.agent_id == agent_id)

    if flagged_only:
        stmt = stmt.join(AgentAction.risk_score).where(RiskScore.flagged == True)

    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    actions = result.scalars().all()

    response = []
    for act in actions:
        rs_resp = RiskScoreResponse.model_validate(act.risk_score) if act.risk_score else None
        response.append(ActionDetailWithScore(
            action=AgentActionResponse.model_validate(act),
            risk_score=rs_resp
        ))

    return response


@router.get(
    "/audit/{action_id}",
    summary="Get audit trail and full breakdown for a specific action"
)
async def get_action_audit(
    action_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves complete audit trail, risk breakdown, and SHAP explanation for a single action."""
    stmt_action = (
        select(AgentAction)
        .options(selectinload(AgentAction.risk_score), selectinload(AgentAction.audit_logs))
        .where(AgentAction.id == action_id)
    )
    res = await db.execute(stmt_action)
    action = res.scalar_one_or_none()

    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action with ID '{action_id}' not found."
        )

    return {
        "action": AgentActionResponse.model_validate(action),
        "risk_score": RiskScoreResponse.model_validate(action.risk_score) if action.risk_score else None,
        "audit_logs": [AuditLogResponse.model_validate(log) for log in action.audit_logs]
    }


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Get high-level trust and fraud metrics"
)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Returns aggregated stats for dashboard cards and reporting."""
    stmt_total = select(func.count(AgentAction.id))
    res_total = await db.execute(stmt_total)
    total_actions = res_total.scalar() or 0

    stmt_flagged = select(func.count(RiskScore.id)).where(RiskScore.flagged == True)
    res_flagged = await db.execute(stmt_flagged)
    flagged_actions = res_flagged.scalar() or 0

    clean_actions = max(0, total_actions - flagged_actions)
    flag_rate = (flagged_actions / total_actions * 100.0) if total_actions > 0 else 0.0

    stmt_avg = select(func.avg(RiskScore.risk_score))
    res_avg = await db.execute(stmt_avg)
    avg_score = res_avg.scalar() or 0.0

    stmt_high = select(func.count(RiskScore.id)).where(RiskScore.risk_level.in_(["HIGH", "CRITICAL"]))
    res_high = await db.execute(stmt_high)
    high_risk_count = res_high.scalar() or 0

    return StatsResponse(
        total_actions=total_actions,
        flagged_actions=flagged_actions,
        clean_actions=clean_actions,
        flag_rate_percentage=round(flag_rate, 2),
        average_risk_score=round(avg_score, 2),
        high_risk_actions=high_risk_count
    )


@router.get("/health", summary="Health check endpoint")
async def health_check():
    return {
        "status": "healthy",
        "service": "Know Your Agent Fraud Detection Layer",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

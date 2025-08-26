
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import AnalyticsQueryAudit


class AnalyticsAuditRepository:
    """Repository for AnalyticsQueryAudit operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def record(
        self,
        user_id: int | None,
        endpoint: str,
        params_json: str | None,
        duration_ms: int | None,
        rows_returned: int | None
    ) -> AnalyticsQueryAudit:
        """Record an analytics query for auditing."""
        audit = AnalyticsQueryAudit(
            user_id=user_id,
            endpoint=endpoint,
            params_json=params_json,
            duration_ms=duration_ms,
            rows_returned=rows_returned
        )
        self.session.add(audit)
        await self.session.commit()
        await self.session.refresh(audit)
        return audit

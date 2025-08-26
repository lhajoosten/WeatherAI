"""LLM audit repository."""

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.infrastructure.db.models import LLMAudit


class LLMAuditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def record(
        self,
        user_id: int | None,
        endpoint: str,
        model: str,
        prompt_summary: str,
        tokens_in: int,
        tokens_out: int,
        cost: float | None = None,
        has_air_quality: bool = False,
        has_astronomy: bool = False,
    ) -> LLMAudit:
        audit = LLMAudit(
            user_id=user_id,
            endpoint=endpoint,
            model=model,
            prompt_summary=prompt_summary[:200],
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost=cost,
            has_air_quality=has_air_quality,
            has_astronomy=has_astronomy,
        )
        self.session.add(audit)
        await self.session.commit()
        await self.session.refresh(audit)
        return audit

    async def get_user_usage_today(self, user_id: int) -> list[LLMAudit]:
        from sqlalchemy import func
        today = datetime.utcnow().date()
        tomorrow = today.replace(day=today.day)  # same day boundary; simple filter by date()
        stmt = select(LLMAudit).where(LLMAudit.user_id == user_id, func.date(LLMAudit.created_at) == today)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

__all__ = ["LLMAuditRepository"]

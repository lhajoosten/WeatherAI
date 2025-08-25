"""Repository for ProviderRun operations."""
import logging
from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ProviderRun

logger = logging.getLogger(__name__)


class ProviderRunRepository:
    """Repository for ProviderRun operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        provider: str,
        run_type: str,
        location_id: int | None = None,
        started_at: datetime | None = None
    ) -> ProviderRun:
        """Create a new provider run record."""
        if started_at is None:
            started_at = datetime.utcnow()

        provider_run = ProviderRun(
            provider=provider,
            run_type=run_type,
            location_id=location_id,
            started_at=started_at,
            status="RUNNING"
        )

        self.session.add(provider_run)
        await self.session.commit()
        await self.session.refresh(provider_run)

        logger.info(f"Created provider run {provider_run.id}: {provider}/{run_type}")
        return provider_run

    async def update_status(
        self,
        run_id: int,
        status: str,
        records_ingested: int | None = None,
        error_message: str | None = None
    ) -> ProviderRun | None:
        """Update provider run status and completion details."""
        stmt = select(ProviderRun).where(ProviderRun.id == run_id)
        result = await self.session.execute(stmt)
        provider_run = result.scalar_one_or_none()

        if provider_run:
            provider_run.status = status
            provider_run.completed_at = datetime.utcnow()
            if records_ingested is not None:
                provider_run.records_ingested = records_ingested
            if error_message is not None:
                provider_run.error_message = error_message

            await self.session.commit()
            await self.session.refresh(provider_run)

            logger.info(f"Updated provider run {run_id}: status={status}, records={records_ingested}")

        return provider_run

    async def get_recent_runs(
        self,
        provider: str | None = None,
        status: str | None = None,
        limit: int = 50
    ) -> list[ProviderRun]:
        """Get recent provider runs with optional filtering."""
        stmt = select(ProviderRun)

        if provider:
            stmt = stmt.where(ProviderRun.provider == provider)
        if status:
            stmt = stmt.where(ProviderRun.status == status)

        stmt = stmt.order_by(desc(ProviderRun.started_at)).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

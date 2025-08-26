from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.infrastructure.db.models import ForecastAccuracy


class AccuracyRepository:
    """Repository for ForecastAccuracy operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        location_id: int,
        target_time: datetime,
        forecast_issue_time: datetime,
        variable: str,
        forecast_value: float | None,
        observed_value: float | None
    ) -> ForecastAccuracy:
        """Create a forecast accuracy record with computed errors."""
        abs_error = None
        pct_error = None

        if forecast_value is not None and observed_value is not None:
            abs_error = abs(forecast_value - observed_value)
            if observed_value != 0:
                pct_error = (abs_error / abs(observed_value)) * 100

        accuracy = ForecastAccuracy(
            location_id=location_id,
            target_time=target_time,
            forecast_issue_time=forecast_issue_time,
            variable=variable,
            forecast_value=forecast_value,
            observed_value=observed_value,
            abs_error=abs_error,
            pct_error=pct_error
        )
        self.session.add(accuracy)
        await self.session.commit()
        await self.session.refresh(accuracy)
        return accuracy

    async def get_by_location_and_period(
        self,
        location_id: int,
        start_time: datetime,
        end_time: datetime,
        variables: list[str] | None = None
    ) -> list[ForecastAccuracy]:
        """Get accuracy records for a location within a time period."""
        stmt = (
            select(ForecastAccuracy)
            .where(ForecastAccuracy.location_id == location_id)
            .where(ForecastAccuracy.target_time >= start_time)
            .where(ForecastAccuracy.target_time <= end_time)
        )

        if variables:
            stmt = stmt.where(ForecastAccuracy.variable.in_(variables))

        stmt = stmt.order_by(ForecastAccuracy.target_time, ForecastAccuracy.variable)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

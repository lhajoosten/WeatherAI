import logging
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import ForecastHourly

logger = logging.getLogger(__name__)


class ForecastRepository:
    """Repository for ForecastHourly operations (analytics variant)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        location_id: int,
        forecast_issue_time: datetime,
        target_time: datetime,
        temp_c: float | None = None,
        precipitation_probability_pct: float | None = None,
        wind_kph: float | None = None,
        model_name: str | None = None,
        source_run_id: str | None = None,
        raw_json: str | None = None
    ) -> ForecastHourly:
        """Create a new forecast record."""
        forecast = ForecastHourly(
            location_id=location_id,
            forecast_issue_time=forecast_issue_time,
            target_time=target_time,
            temp_c=temp_c,
            precipitation_probability_pct=precipitation_probability_pct,
            wind_kph=wind_kph,
            model_name=model_name,
            source_run_id=source_run_id,
            raw_json=raw_json
        )
        self.session.add(forecast)
        await self.session.commit()
        await self.session.refresh(forecast)
        return forecast

    async def get_by_location_and_period(
        self,
        location_id: int,
        start_target_time: datetime,
        end_target_time: datetime,
        limit: int = 1000
    ) -> list[ForecastHourly]:
        """Get forecasts for a location within a target time period."""
        stmt = (
            select(ForecastHourly)
            .where(ForecastHourly.location_id == location_id)
            .where(ForecastHourly.target_time >= start_target_time)
            .where(ForecastHourly.target_time <= end_target_time)
            .order_by(ForecastHourly.target_time, ForecastHourly.forecast_issue_time)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def bulk_upsert(self, records: list[dict[str, Any]]) -> int:
        """Bulk upsert forecast records with deduplication by (location_id, target_time, model_name)."""
        if not records:
            return 0

        upserted_count = 0

        for record in records:
            try:
                # Check if record exists with same location, target time, and model
                stmt = select(ForecastHourly).where(
                    ForecastHourly.location_id == record["location_id"],
                    ForecastHourly.target_time == record["target_time"],
                    ForecastHourly.model_name == record.get("model_name")
                )
                result = await self.session.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    # Update existing record with newer forecast_issue_time
                    if record["forecast_issue_time"] > existing.forecast_issue_time:
                        for key, value in record.items():
                            if key not in ["location_id", "target_time", "model_name"]:
                                setattr(existing, key, value)
                else:
                    # Create new record
                    new_record = ForecastHourly(**record)
                    self.session.add(new_record)

                upserted_count += 1

            except Exception as e:
                logger.warning(f"Error upserting forecast record: {e}")
                continue

        await self.session.commit()
        logger.info(f"Bulk upserted {upserted_count}/{len(records)} forecast records")
        return upserted_count

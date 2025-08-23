from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models import ForecastHourly


class ForecastRepository:
    """Repository for ForecastHourly operations (analytics variant)."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        location_id: int,
        forecast_issue_time: datetime,
        target_time: datetime,
        temp_c: Optional[float] = None,
        precipitation_probability_pct: Optional[float] = None,
        wind_kph: Optional[float] = None,
        model_name: Optional[str] = None,
        source_run_id: Optional[str] = None,
        raw_json: Optional[str] = None
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
    ) -> List[ForecastHourly]:
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
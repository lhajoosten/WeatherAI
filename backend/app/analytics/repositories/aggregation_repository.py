from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models import AggregationDaily


class AggregationRepository:
    """Repository for AggregationDaily operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_or_update(
        self,
        location_id: int,
        date: datetime,
        temp_min_c: Optional[float] = None,
        temp_max_c: Optional[float] = None,
        avg_temp_c: Optional[float] = None,
        total_precip_mm: Optional[float] = None,
        max_wind_kph: Optional[float] = None,
        heating_degree_days: Optional[float] = None,
        cooling_degree_days: Optional[float] = None
    ) -> AggregationDaily:
        """Create or update a daily aggregation record (idempotent)."""
        # Check if record exists
        stmt = select(AggregationDaily).where(
            AggregationDaily.location_id == location_id,
            AggregationDaily.date == date
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing record
            existing.temp_min_c = temp_min_c
            existing.temp_max_c = temp_max_c
            existing.avg_temp_c = avg_temp_c
            existing.total_precip_mm = total_precip_mm
            existing.max_wind_kph = max_wind_kph
            existing.heating_degree_days = heating_degree_days
            existing.cooling_degree_days = cooling_degree_days
            existing.generated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        else:
            # Create new record
            aggregation = AggregationDaily(
                location_id=location_id,
                date=date,
                temp_min_c=temp_min_c,
                temp_max_c=temp_max_c,
                avg_temp_c=avg_temp_c,
                total_precip_mm=total_precip_mm,
                max_wind_kph=max_wind_kph,
                heating_degree_days=heating_degree_days,
                cooling_degree_days=cooling_degree_days
            )
            self.session.add(aggregation)
            await self.session.commit()
            await self.session.refresh(aggregation)
            return aggregation
    
    async def get_by_location_and_period(
        self,
        location_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[AggregationDaily]:
        """Get daily aggregations for a location within a date range."""
        stmt = (
            select(AggregationDaily)
            .where(AggregationDaily.location_id == location_id)
            .where(AggregationDaily.date >= start_date)
            .where(AggregationDaily.date <= end_date)
            .order_by(AggregationDaily.date)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
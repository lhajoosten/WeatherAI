"""Repository for AirQualityHourly operations."""
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert as mssql_insert

from app.db.models import AirQualityHourly

logger = logging.getLogger(__name__)


class AirQualityRepository:
    """Repository for AirQualityHourly operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        location_id: int,
        observed_at: datetime,
        pm10: float | None = None,
        pm2_5: float | None = None,
        ozone: float | None = None,
        no2: float | None = None,
        so2: float | None = None,
        pollen_tree: float | None = None,
        pollen_grass: float | None = None,
        pollen_weed: float | None = None,
        source: str = "openmeteo",
        raw_json: str | None = None
    ) -> AirQualityHourly:
        """Create a new air quality record."""
        air_quality = AirQualityHourly(
            location_id=location_id,
            observed_at=observed_at,
            pm10=pm10,
            pm2_5=pm2_5,
            ozone=ozone,
            no2=no2,
            so2=so2,
            pollen_tree=pollen_tree,
            pollen_grass=pollen_grass,
            pollen_weed=pollen_weed,
            source=source,
            raw_json=raw_json
        )
        
        self.session.add(air_quality)
        await self.session.commit()
        await self.session.refresh(air_quality)
        
        return air_quality

    async def bulk_upsert(self, records: list[dict[str, Any]]) -> int:
        """Bulk upsert air quality records using MERGE pattern."""
        if not records:
            return 0

        try:
            # Use MSSQL-specific MERGE via raw SQL for better performance
            # First, convert records to a format suitable for bulk insert
            insert_stmt = mssql_insert(AirQualityHourly)
            
            # MSSQL upsert: INSERT with ON CONFLICT UPDATE
            upsert_stmt = insert_stmt.on_duplicate_key_update(
                pm10=insert_stmt.inserted.pm10,
                pm2_5=insert_stmt.inserted.pm2_5,
                ozone=insert_stmt.inserted.ozone,
                no2=insert_stmt.inserted.no2,
                so2=insert_stmt.inserted.so2,
                pollen_tree=insert_stmt.inserted.pollen_tree,
                pollen_grass=insert_stmt.inserted.pollen_grass,
                pollen_weed=insert_stmt.inserted.pollen_weed,
                raw_json=insert_stmt.inserted.raw_json
            )
            
            await self.session.execute(upsert_stmt, records)
            await self.session.commit()
            
            logger.info(f"Bulk upserted {len(records)} air quality records")
            return len(records)
            
        except Exception as e:
            logger.error(f"Error in bulk upsert air quality: {e}")
            await self.session.rollback()
            # Fallback to individual inserts with conflict handling
            return await self._fallback_upsert(records)

    async def _fallback_upsert(self, records: list[dict[str, Any]]) -> int:
        """Fallback upsert method using individual operations."""
        upserted_count = 0
        
        for record in records:
            try:
                # Check if record exists
                stmt = select(AirQualityHourly).where(
                    AirQualityHourly.location_id == record["location_id"],
                    AirQualityHourly.observed_at == record["observed_at"],
                    AirQualityHourly.source == record["source"]
                )
                result = await self.session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if existing:
                    # Update existing record
                    for key, value in record.items():
                        if key not in ["location_id", "observed_at", "source"]:
                            setattr(existing, key, value)
                else:
                    # Create new record
                    new_record = AirQualityHourly(**record)
                    self.session.add(new_record)
                
                upserted_count += 1
                
            except Exception as e:
                logger.warning(f"Error upserting air quality record: {e}")
                continue
        
        await self.session.commit()
        logger.info(f"Fallback upserted {upserted_count}/{len(records)} air quality records")
        return upserted_count

    async def get_by_location_and_period(
        self,
        location_id: int,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000
    ) -> list[AirQualityHourly]:
        """Get air quality data for a location within a time period."""
        stmt = select(AirQualityHourly).where(
            AirQualityHourly.location_id == location_id,
            AirQualityHourly.observed_at >= start_time,
            AirQualityHourly.observed_at <= end_time
        ).order_by(AirQualityHourly.observed_at).limit(limit)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
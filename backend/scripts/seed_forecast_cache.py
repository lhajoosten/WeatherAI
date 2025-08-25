import asyncio
import json
from datetime import datetime, timedelta
import sqlalchemy as sa

from app.db.models import ForecastCache, Location
from backend.app.db.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as session:
        locs = (await session.execute(sa.select(Location))).scalars().all()
        if not locs:
            print("No locations found; run seed_basic first.")
            return

        for loc in locs:
            existing = (await session.execute(
                sa.select(ForecastCache).where(ForecastCache.location_id == loc.id)
            )).scalar_one_or_none()
            if existing:
                continue
            payload = {
                "generated_at": datetime.utcnow().isoformat(),
                "hours": [
                    {
                        "time": (datetime.utcnow() + timedelta(hours=i)).isoformat(),
                        "temp_c": 15 + 0.2 * i,
                        "wind_kph": 5 + (i % 4),
                        "precip_mm": 0.2 if i % 6 == 0 else 0.0
                    } for i in range(24)
                ]
            }
            cache = ForecastCache(
                location_id=loc.id,
                source="seed-demo",
                fetched_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=6),
                payload_json=json.dumps(payload)
            )
            session.add(cache)
            print(f"Inserted forecast cache for location {loc.id}")
        await session.commit()
    print("Forecast cache seed complete.")

if __name__ == "__main__":
    asyncio.run(main())
import asyncio
from datetime import datetime
import sqlalchemy as sa

from backend.app.db.database import AsyncSessionLocal
from backend.app.db.models import Location, User

async def main():
    async with AsyncSessionLocal() as session:
        user = await session.get(User, 1)
        if not user:
            user = User(
                id=1,
                email="demo@example.com",
                password_hash="dev",
                timezone="UTC",
                created_at=datetime.utcnow()
            )
            session.add(user)
            await session.commit()
            print("Inserted demo user id=1")

        existing = (await session.execute(
            sa.select(Location).where(Location.user_id == 1)
        )).scalars().all()

        if not existing:
            session.add_all([
                Location(user_id=1, name="Amsterdam", lat=52.37, lon=4.90, timezone="Europe/Amsterdam"),
                Location(user_id=1, name="Rotterdam", lat=51.92, lon=4.48, timezone="Europe/Amsterdam"),
                Location(user_id=1, name="Utrecht", lat=52.09, lon=5.12, timezone="Europe/Amsterdam"),
            ])
            await session.commit()
            print("Inserted 3 locations")

    print("Basic seed complete.")

if __name__ == "__main__":
    asyncio.run(main())
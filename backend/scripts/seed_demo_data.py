import asyncio
from datetime import datetime, timedelta
import random
import json
import sqlalchemy as sa

from app.db.session import async_session
from app.db.models import User  # aanname
from app.db.models.location import Location  # aanname
from app.db.models.user_preferences import UserPreferences  # aanname
from app.db.models.digest_audit import DigestAudit  # nieuw
from app.db.models.observation import Observation  # aanname of forecast table
from app.core.config import settings

USERS = [
    {"email": "demo@example.com", "timezone": "Europe/Amsterdam"},
    {"email": "alice@example.com", "timezone": "Europe/London"},
    {"email": "bob@example.com", "timezone": "America/New_York"},
]

LOCATIONS = [
    ("Amsterdam", 52.37, 4.90, "Europe/Amsterdam"),
    ("London", 51.50, -0.12, "Europe/London"),
    ("New York", 40.71, -74.00, "America/New_York"),
]

async def ensure_users(session):
    created = 0
    for u in USERS:
        existing = (await session.execute(
            sa.select(User).where(User.email == u["email"])
        )).scalar_one_or_none()
        if not existing:
            user = User(email=u["email"], password_hash="dev", timezone=u["timezone"], created_at=datetime.utcnow())
            session.add(user)
            created += 1
    if created:
        await session.commit()
    return created

async def ensure_locations(session):
    users = (await session.execute(sa.select(User))).scalars().all()
    for user in users:
        for name, lat, lon, tz in LOCATIONS:
            existing = (await session.execute(
                sa.select(Location).where(Location.user_id == user.id, Location.name == name)
            )).scalar_one_or_none()
            if not existing:
                session.add(Location(user_id=user.id, name=name, lat=lat, lon=lon, timezone=tz, created_at=datetime.utcnow()))
    await session.commit()

async def ensure_preferences(session):
    users = (await session.execute(sa.select(User))).scalars().all()
    for user in users:
        pref = (await session.execute(
            sa.select(UserPreferences).where(UserPreferences.user_id == user.id)
        )).scalar_one_or_none()
        if not pref:
            session.add(UserPreferences(
                user_id=user.id,
                temperature_tolerance=random.choice(["low", "normal", "high"]),
                rain_tolerance=random.choice(["low", "medium", "high"]),
                outdoor_activities=random.choice([True, False]),
                units_system="metric"
            ))
    await session.commit()

async def ensure_observations(session, hours=36):
    # Aanname: Observation model met fields: location_id, observed_at, temp_c, wind_kph, precip_mm, humidity_pct, condition_code, source
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    locations = (await session.execute(sa.select(Location))).scalars().all()
    for loc in locations:
        for h in range(hours):
            ts = now + timedelta(hours=h)
            existing = (await session.execute(
                sa.select(Observation).where(Observation.location_id == loc.id, Observation.observed_at == ts)
            )).scalar_one_or_none()
            if existing:
                continue
            session.add(Observation(
                location_id=loc.id,
                observed_at=ts,
                temp_c=15 + 8 * (1 - abs((h % 24) - 12)/12),  # simpele dagcurve
                wind_kph=5 + (h % 6),
                precip_mm=0.2 if (h % 7 == 0) else 0,
                humidity_pct=60 + (h % 10),
                condition_code="sun" if h % 5 else "cloud",
                source="seed"
            ))
    await session.commit()

async def ensure_digest_audit_samples(session, days=3):
    users = (await session.execute(sa.select(User))).scalars().all()
    today = datetime.utcnow().date()
    for user in users:
        for d in range(days):
            target_date = today - timedelta(days=d)
            existing = (await session.execute(
                sa.select(DigestAudit).where(DigestAudit.user_id == user.id, DigestAudit.date == target_date)
            )).scalar_one_or_none()
            if existing:
                continue
            session.add(DigestAudit(
                user_id=user.id,
                date=target_date,
                cache_hit=False,
                forecast_signature="seed_sig",
                preferences_hash="seed_pref",
                prompt_version="digest_v1_1",
                model_name="gpt-4o-mini",
                tokens_in=900,
                tokens_out=140,
                latency_ms_preprocess=220,
                latency_ms_llm=480,
                latency_ms_total=730,
                comfort_score=0.78,
                temp_peak_c=23.5,
                temp_peak_hour=15,
                wind_peak_kph=18.0,
                wind_peak_hour=16,
                rain_windows_json=json.dumps([]),
                activity_block_json=json.dumps({"start_hour":9,"end_hour":11,"score":0.92})
            ))
    await session.commit()

async def main():
    if not getattr(settings, "allow_seed", True):
        print("Seeding disabled by settings.")
        return
    async with async_session() as session:
        await ensure_users(session)
        await ensure_locations(session)
        await ensure_preferences(session)
        await ensure_observations(session)
        await ensure_digest_audit_samples(session)
    print("Seed complete.")

if __name__ == "__main__":
    asyncio.run(main())
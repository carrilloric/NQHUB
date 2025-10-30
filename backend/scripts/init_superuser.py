"""
Create initial superuser
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.db.session import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from sqlalchemy import select


async def create_superuser():
    """Create initial superuser"""
    print("Creating superuser...")
    print(f"Email: {settings.SUPERUSER_EMAIL}")

    async with AsyncSessionLocal() as session:
        # Check if superuser exists
        result = await session.execute(
            select(User).where(User.email == settings.SUPERUSER_EMAIL)
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"✅ Superuser {settings.SUPERUSER_EMAIL} already exists")
            return

        # Create superuser
        superuser = User(
            email=settings.SUPERUSER_EMAIL,
            hashed_password=get_password_hash(settings.SUPERUSER_PASSWORD),
            full_name="Super User",
            role=UserRole.SUPERUSER,
            is_active=True,
            is_verified=True
        )
        session.add(superuser)
        await session.commit()
        print(f"✅ Superuser created: {settings.SUPERUSER_EMAIL}")
        print(f"   Password: {settings.SUPERUSER_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(create_superuser())

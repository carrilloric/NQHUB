"""
Create initial superuser
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings

# TODO: Uncomment when models are implemented
# from app.db.session import get_session
# from app.models.user import User
# from app.core.security import get_password_hash
# from sqlalchemy import select


async def create_superuser():
    """Create initial superuser"""
    print("Creating superuser...")
    print(f"Email: {settings.SUPERUSER_EMAIL}")

    # TODO: Implement when database models are ready
    print("⚠️  Database models not yet implemented")
    print("This script will create superuser once models are set up")

    # Example implementation (uncomment when models are ready):
    """
    async with get_session() as session:
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
            first_name="Super",
            last_name="User",
            role="superuser",
            is_active=True
        )
        session.add(superuser)
        await session.commit()
        print(f"✅ Superuser created: {settings.SUPERUSER_EMAIL}")
    """


if __name__ == "__main__":
    asyncio.run(create_superuser())

"""
Generate invitation token
"""
import asyncio
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import uuid

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings

# TODO: Uncomment when models are implemented
# from app.db.session import get_session
# from app.models.invitation import Invitation


async def generate_invitation(email: str = None, role: str = "trader", days: int = 7):
    """Generate invitation token"""
    print("Generating invitation...")
    print(f"Role: {role}")
    if email:
        print(f"Pre-assigned to: {email}")
    print(f"Expires in: {days} days")

    # Generate token
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(days=days)

    print(f"\n✅ Invitation token: {token}")
    print(f"Expires at: {expires_at}")
    print(f"\nInvitation URL: http://localhost:3000/register?token={token}")

    # TODO: Implement when database models are ready
    print("\n⚠️  Database models not yet implemented")
    print("Token generated but not saved to database")

    # Example implementation (uncomment when models are ready):
    """
    async with get_session() as session:
        invitation = Invitation(
            token=token,
            email=email,
            role=role,
            expires_at=expires_at,
            # invited_by will be set when we have auth
        )
        session.add(invitation)
        await session.commit()
        print("✅ Invitation saved to database")
    """


def main():
    parser = argparse.ArgumentParser(description="Generate invitation token")
    parser.add_argument("--email", help="Pre-assign to email", default=None)
    parser.add_argument("--role", help="Role for user", default="trader", choices=["superuser", "trader"])
    parser.add_argument("--days", help="Days until expiration", type=int, default=7)

    args = parser.parse_args()

    asyncio.run(generate_invitation(args.email, args.role, args.days))


if __name__ == "__main__":
    main()

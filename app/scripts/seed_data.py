import asyncio

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models import Gender, Profile, Role, Status
from app.repositories.profile_likes import ProfileLikeRepository
from app.repositories.profiles import ProfileRepository


async def seed_demo_user(repository: ProfileRepository) -> None:
    if not settings.demo_user_enabled:
        return

    if settings.demo_email is None or settings.demo_password is None:
        raise RuntimeError("DEMO_EMAIL and DEMO_PASSWORD must be set when demo user is enabled")

    if await repository.exists_by_email(settings.demo_email):
        return

    profile = Profile(
        email=settings.demo_email,
        password=hash_password(settings.demo_password),
        name="Demo",
        surname="User",
        status=Status.ACTIVE,
        role=Role.USER,
    )

    repository.session.add(profile)


async def seed_synthetic_users(repository: ProfileRepository) -> None:
    if not settings.synthetic_users_enabled:
        return

    if settings.synthetic_users_password is None:
        raise RuntimeError("SYNTHETIC_USERS_PASSWORD must be set when synthetic users are enabled")

    password_hash = hash_password(settings.synthetic_users_password)

    for index in range(1, settings.synthetic_users_count + 1):
        email = f"{settings.synthetic_users_email_prefix}{index}@example.com"

        if await repository.exists_by_email(email):
            continue

        profile = Profile(
            email=email,
            password=password_hash,
            name=f"User {index}",
            surname="Synthetic",
            about=f"Synthetic profile #{index}",
            gender=Gender.MALE if index % 2 else Gender.FEMALE,
            status=Status.ACTIVE,
            role=Role.USER,
        )

        repository.session.add(profile)


async def seed_synthetic_likes_to_demo(
    profile_repository: ProfileRepository,
    like_repository: ProfileLikeRepository,
) -> None:
    if (
        not settings.demo_user_enabled
        or not settings.synthetic_users_enabled
        or settings.demo_email is None
    ):
        return

    demo_profile = await profile_repository.get_by_email(settings.demo_email)

    if demo_profile is None:
        return

    for index in range(1, settings.synthetic_users_count + 1):
        if index % 3 != 0:
            continue

        email = f"{settings.synthetic_users_email_prefix}{index}@example.com"
        synthetic_profile = await profile_repository.get_by_email(email)

        if synthetic_profile is None:
            continue

        await like_repository.set_like(
            from_profile_id=synthetic_profile.id,
            to_profile_id=demo_profile.id,
            liked=True,
        )


async def main() -> None:
    async with AsyncSessionLocal() as session:
        profile_repository = ProfileRepository(session)
        like_repository = ProfileLikeRepository(session)

        await seed_demo_user(profile_repository)
        await seed_synthetic_users(profile_repository)
        await session.flush()

        await seed_synthetic_likes_to_demo(profile_repository, like_repository)

        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())

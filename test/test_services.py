import pytest
from repositories.users import UsersRepository
from models.users import Users, Roles
from services.users import UsersService


@pytest.mark.asyncio
async def test_sub_unsub_service(db):
    role = Roles(name="admin")
    user1 = Users(login="admin", password="123", email="e@e.com", name="admin", pfp="m", role_id=1, is_banned=False, ban_reason=None, is_verified=True, verification_token="sa")
    user2 = Users(login="abby", password="123", email="e@1e.com", name="abby", pfp="a", role_id=1, is_banned=False,ban_reason=None, is_verified=True, verification_token="sa4")
    db.add_all([user1, user2, role])
    await db.commit()
    await db.refresh(user1)
    await db.refresh(user2)
    await db.refresh(role)

    await UsersService.sub_unsub(user1.id, user2.id, db)
    sub = await UsersRepository.get_follow(user1.id, user2.id, db)
    assert sub is not None

    await UsersService.sub_unsub(user1.id, user2.id, db)
    sub = await UsersRepository.get_follow(user1.id, user2.id, db)
    assert sub is None
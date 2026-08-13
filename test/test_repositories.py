import pytest

from repositories.admin_forum import AdminForumRepository
from repositories.forum import ForumRepository
from repositories.users import UsersRepository
from models.users import Users, Roles
from services.forum import ForumService
from services.users import UsersService

@pytest.mark.asyncio
async def test_post_delete(db, current_user):
    role = Roles(name="admin")
    user1 = Users(login="admin", password="123", email="e@e.com", name="admin", pfp="m", role_id=1, is_banned=False, ban_reason=None, is_verified=True, verification_token="sa")
    user2 = Users(login="abby", password="123", email="e@1e.com", name="abby", pfp="a", role_id=1, is_banned=False, ban_reason=None, is_verified=True, verification_token="sa4")
    db.add_all([user1, user2, role])
    await db.commit()
    await db.refresh(user1)
    await db.refresh(user2)
    await db.refresh(role)

    await AdminForumRepository.create_category("n", 1, db)
    await AdminForumRepository.create_subcategory("n1", 1, None, 1)
    post = await ForumRepository.create_post("n", "nnnnn", 1, current_user, db)
    await ForumRepository.add_post_img("sss", post.id, db)
    await ForumRepository.add_post_img("aaa", post.id, db)
    await ForumRepository.add_post_img("bbb", post.id, db)
    delete = await ForumService.delete_post(post.id, db, current_user)

    assert delete is True
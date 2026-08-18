import pytest

from repositories.admin_forum import AdminForumRepository
from repositories.forum import ForumRepository
from repositories.users import UsersRepository
from models.users import Users, Roles
from services.forum import ForumService
from services.users import UsersService

@pytest.mark.asyncio
async def test_get_pid_by_cid(db, current_user):
    role = Roles(name="admin")
    user1 = Users(login="admin", password="123", email="e@e.com", name="admin", pfp="m", role_id=1, is_banned=False, ban_reason=None, is_verified=True, verification_token="sa")
    db.add_all([user1, role])
    await db.commit()
    await db.refresh(user1)
    await db.refresh(role)

    await AdminForumRepository.create_category("n", 1, db)
    await AdminForumRepository.create_subcategory("n1", 1, None, db)
    post = await ForumRepository.create_post("n", "nnnnn", 1, 1, current_user, db)
    comments = await ForumRepository.create_comment("buba", post.id, 1, db, current_user)
    post_by_cid = await ForumRepository.get_post_by_cid(comments.id, db)

    assert post_by_cid is post.id
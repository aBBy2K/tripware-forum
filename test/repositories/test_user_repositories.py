import pytest
from sqlalchemy.exc import SQLAlchemyError
from repositories.users import UsersRepository

@pytest.mark.asyncio
async def test_get_by_id(db, current_user, user, roles):
    db_user = await UsersRepository.get_by_id(db=db, uid=current_user.id)

    assert db_user.id is current_user.id
    assert db_user.login is current_user.login

@pytest.mark.asyncio
async def test_get_by_id_not_exists(db, current_user):
    user = await UsersRepository.get_by_id(db=db, uid=0)

    assert user is None

@pytest.mark.asyncio
async def test_create_new(db, roles):
    user = await UsersRepository.create_user(login="bbb", password="123", email="n@n1.com", name="s2", token="da", db=db)

    assert user is not None

@pytest.mark.asyncio
async def test_create_new_exist(db, roles):
    await UsersRepository.create_user(login="bbb", password="123", email="n@n1.com", name="s2", token="da", db=db)

    with pytest.raises(SQLAlchemyError):
        await UsersRepository.create_user(login="bbb", password="123", email="n@n1.com", name="s2", token="da", db=db)

@pytest.mark.asyncio
async def test_sub(db, current_user, user):
    await UsersRepository.subscribe(user.id, current_user.id, db)

    subs = await UsersRepository.get_followers(current_user.id, db)
    subscriptions = await UsersRepository.get_followings(user.id, db)

    assert subs[0] == user.id
    assert subscriptions[0] == current_user.id

@pytest.mark.asyncio
async def test_unsub(db, current_user, user):
    sub = await UsersRepository.subscribe(user.id, current_user.id, db)

    assert sub.follower_id == user.id

    await UsersRepository.unsubscribe(user.id, current_user.id, db)

    subs = await UsersRepository.get_followers(current_user.id, db)

    assert not subs

@pytest.mark.asyncio
async def test_set_chat_id(db, current_user):
    is_set = await UsersRepository.set_tg_chatid(123, current_user.id, db)

    assert is_set is True

@pytest.mark.asyncio
async def test_set_chat_id_exists(db, current_user, user):
    await UsersRepository.set_tg_chatid(123, current_user.id, db)
    
    with pytest.raises(SQLAlchemyError):
        await UsersRepository.set_tg_chatid(123, user.id, db)

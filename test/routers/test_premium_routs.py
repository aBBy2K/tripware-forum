import pytest

@pytest.mark.asyncio
async def test_premium_user(current_user, roles, client, subcategories, token, db):
    current_user.role_id = roles["premium"].id
    await db.commit()

    client.cookies.set("token", token)

    response = await client.get(f"/forum/sc/{subcategories["discussion"].id}")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_user(current_user, roles, client, subcategories, token, db):
    client.cookies.set("token", token)

    response = await client.get(f"/forum/sc/{subcategories["discussion"].id}")
    assert response.status_code == 307

@pytest.mark.asyncio
async def test_banned_user(current_user, roles, client, subcategories, token, db):
    current_user.is_banned = True
    await db.commit()
    
    client.cookies.set("token", token)

    response = await client.get(f"/forum/sc/{subcategories["discussion"].id}")
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_unauthed(client, subcategories, db):
    response = await client.get(f"/forum/sc/{subcategories["discussion"].id}")
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_invalid_token(current_user, roles, client, subcategories, db):
    client.cookies.set("token", "123")

    with pytest.raises(AttributeError):
        response = await client.get(f"/forum/sc/{subcategories["discussion"].id}")
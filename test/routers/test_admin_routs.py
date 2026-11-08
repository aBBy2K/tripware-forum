import pytest

@pytest.mark.asyncio
async def test_admin(current_user, roles, token, db, client):
    client.cookies.set("token", token)

    current_user.role_id = roles["admin"].id
    await db.commit()

    response = await client.get("/admin/")

    assert response.status_code == 200

@pytest.mark.asyncio
async def test_premium(current_user, roles, token, db, client):
    client.cookies.set("token", token)

    current_user.role_id = roles["premium"].id
    await db.commit()

    response = await client.get("/admin/")

    assert response.status_code == 403

@pytest.mark.asyncio
async def test_user(current_user, roles, token, db, client):
    client.cookies.set("token", token)

    current_user.role_id = roles["user"].id
    await db.commit()

    response = await client.get("/admin/")

    assert response.status_code == 403
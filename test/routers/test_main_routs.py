import pytest
from security.auth import create_access_key

@pytest.mark.asyncio
async def test_index_noauth(client):
    response = await client.get("/")

    assert response.status_code == 200

@pytest.mark.asyncio
async def test_index_auth(client, current_user, token):
    client.cookies.set("token", token)
    response = await client.get("/")

    assert response.status_code == 200

@pytest.mark.asyncio
async def test_index_banned(client, current_user, token, db):
    client.cookies.set("token", token)

    current_user.is_banned = True
    await db.commit()

    response = await client.get("/")

    assert response.status_code == 403
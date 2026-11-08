import pytest
from unittest.mock import ANY, patch
from services.auth_service import AuthService

@pytest.mark.asyncio
async def test_register(db, roles):
    with patch("services.auth_service.send_mail.delay") as mock:
        result = await AuthService.register(login="admin12345", password="asdsadSsa98$", c_password="asdsadSsa98$", email="test@example.com", name="admin12345", db=db)
        assert result["success"] is True

        mock.assert_called_once_with(subject="tripware / verification email", body=ANY, email="test@example.com")

@pytest.mark.asyncio
async def test_login(db, current_user):
    with patch("services.auth_service.create_access_key") as mock:
        result = await AuthService.login(current_user.login, "123", db)

        assert result["success"] is True

        mock.assert_called_with(data={"sub": str(current_user.id)})
"""Test the CustomHTTPBearer class in the auth_manager module."""
from datetime import datetime

import jwt
import pytest
import sqlalchemy
from fastapi import BackgroundTasks, HTTPException

from config.settings import get_settings
from managers.auth import CustomHTTPBearer, ResponseMessages
from managers.user import UserManager


@pytest.mark.unit()
class TestCustomHTTPBearer:
    """Test the CustomHTTPBearer class."""

    test_user = {
        "email": "testuser@usertest.com",
        "password": "test12345!",
        "first_name": "Test",
        "last_name": "User",
    }

    @pytest.mark.asyncio()
    async def test_custom_bearer_class(self, get_db, mocker):
        """Test with valid user and token."""
        token, _ = await UserManager.register(self.test_user, get_db)
        mock_req = mocker.patch("managers.auth.Request")
        mock_req.headers = {"Authorization": f"Bearer {token}"}

        bearer = CustomHTTPBearer()
        result = await bearer(request=mock_req, db=get_db)

        assert isinstance(result, sqlalchemy.engine.row.Row)
        assert result.email == self.test_user["email"]
        assert result.id == 1

    @pytest.mark.asyncio()
    async def test_custom_bearer_class_invalid_token(self, get_db, mocker):
        """Test with an invalid token."""
        mock_req = mocker.patch("managers.auth.Request")
        mock_req.headers = {"Authorization": "Bearer badtoken"}

        bearer = CustomHTTPBearer()
        with pytest.raises(HTTPException) as exc:
            await bearer(request=mock_req, db=get_db)

        assert exc.value.status_code == 401
        assert exc.value.detail == ResponseMessages.INVALID_TOKEN

    @pytest.mark.asyncio()
    async def test_custom_bearer_class_empty_no_header(self, get_db, mocker):
        """Test with an empty token."""
        mock_req = mocker.patch("managers.auth.Request")
        mock_req.headers = {}

        bearer = CustomHTTPBearer()
        with pytest.raises(HTTPException) as exc:
            await bearer(request=mock_req, db=get_db)

        assert exc.value.status_code == 403
        assert exc.value.detail == "Not authenticated"

    @pytest.mark.asyncio()
    async def test_custom_bearer_class_banned_user(self, get_db, mocker):
        """Test with a banned user."""
        token, _ = await UserManager.register(self.test_user, get_db)
        await UserManager.set_ban_status(1, True, 666, get_db)

        mock_req = mocker.patch("managers.auth.Request")
        mock_req.headers = {"Authorization": f"Bearer {token}"}

        bearer = CustomHTTPBearer()
        with pytest.raises(HTTPException) as exc:
            await bearer(request=mock_req, db=get_db)

        assert exc.value.status_code == 401
        assert exc.value.detail == ResponseMessages.INVALID_TOKEN

    @pytest.mark.asyncio()
    async def test_custom_bearer_class_unverified_user(self, get_db, mocker):
        """Test with a banned user."""
        background_tasks = BackgroundTasks()
        token, _ = await UserManager.register(
            self.test_user, get_db, background_tasks=background_tasks
        )
        await UserManager.set_ban_status(1, True, 666, get_db)

        mock_req = mocker.patch("managers.auth.Request")
        mock_req.headers = {"Authorization": f"Bearer {token}"}

        bearer = CustomHTTPBearer()
        with pytest.raises(HTTPException) as exc:
            await bearer(request=mock_req, db=get_db)

        assert exc.value.status_code == 401
        assert exc.value.detail == ResponseMessages.INVALID_TOKEN

    @pytest.mark.asyncio()
    async def test_custom_bearer_expired_token(self, get_db, mocker):
        """Test with an expired token."""
        expired_token = jwt.encode(
            {
                "sub": 1,
                "exp": datetime.utcnow().timestamp() - 1,
                "typ": "verify",
            },
            get_settings().secret_key,
            algorithm="HS256",
        )

        mock_req = mocker.patch("managers.auth.Request")
        mock_req.headers = {"Authorization": f"Bearer {expired_token}"}

        bearer = CustomHTTPBearer()
        with pytest.raises(HTTPException) as exc:
            await bearer(request=mock_req, db=get_db)

        assert exc.value.status_code == 401
        assert exc.value.detail == ResponseMessages.EXPIRED_TOKEN

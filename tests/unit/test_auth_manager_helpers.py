"""Test the AuthManager class."""
import pytest
from fastapi import HTTPException

from managers.auth import can_edit_user, is_admin, is_banned
from models.enums import RoleType


@pytest.fixture()
def mock_req(mocker):
    """Fixture to return a mocked Request object."""
    request_mock_path = "managers.auth.Request"
    return mocker.patch(request_mock_path)


class TestAuthManagerHelpers:
    """Test the AuthManager class."""

    # ----------------- test the dependency_injector helpers ----------------- #
    def test_is_admin_allow_admin(self, mock_req):
        """Test the is_admin method returns no exception for admin users."""
        mock_req.state.user = {"role": RoleType.admin}

        assert is_admin(mock_req) is None

    def test_is_admin_block_non_admin(self, mock_req):
        """Test the is_admin method returns an exception for non-admin users."""
        mock_req.state.user = {"role": RoleType.user}

        with pytest.raises(HTTPException, match="Forbidden"):
            is_admin(mock_req)

    def test_is_banned_blocks_banned_user(self, mock_req):
        """Test the is_banned method blocks banned users."""
        mock_req.state.user = {"banned": True}

        with pytest.raises(HTTPException, match="Banned!"):
            is_banned(mock_req)

    def test_is_banned_ignores_valid_user(self, mock_req):
        """Test the is_banned method allows non-banned users through."""
        mock_req.state.user = {"banned": False}

        assert is_banned(mock_req) is None

    def test_can_edit_user_allow_admin(self, mock_req):
        """Test the can_edit_user method returns no exception for admin."""
        mock_req.state.user = {"role": RoleType.admin, "id": 2}
        mock_req.path_params = {"user_id": 1}

        assert can_edit_user(mock_req) is None

    def test_can_edit_user_allow_owner(self, mock_req):
        """Test the can_edit_user method returns no exception for the owner."""
        mock_req.state.user = {"role": RoleType.user, "id": 1}
        mock_req.path_params = {"user_id": 1}

        assert can_edit_user(mock_req) is None

    def test_can_edit_user_block_non_admin(self, mock_req):
        """Test the can_edit_user method returns an exception for non-admin."""
        mock_req.state.user = {"role": RoleType.user, "id": 2}
        mock_req.path_params = {"user_id": 1}

        with pytest.raises(HTTPException, match="Forbidden"):
            can_edit_user(mock_req)

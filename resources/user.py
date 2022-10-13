"""Routes for User listing and control."""
from typing import List, Optional

from fastapi import APIRouter, Depends

from managers.auth import is_admin, oauth2_schema
from managers.user import UserManager
from models.enums import RoleType
from schemas.request.user import UserEditRequest
from schemas.response.user import UserResponse

router = APIRouter(tags=["Users"])


@router.get(
    "/users/",
    dependencies=[Depends(oauth2_schema), Depends(is_admin)],
    response_model=List[UserResponse],
)
async def get_users(user_id: Optional[int] = None):
    """Get all users or a specific user by their ID."""
    if user_id:
        return await UserManager.get_user_by_id(user_id)
    return await UserManager.get_all_users()


@router.put(
    "/users/{user_id}/make-admin",
    dependencies=[Depends(oauth2_schema), Depends(is_admin)],
    status_code=204,
)
async def make_admin(user_id: int):
    """Make the User with this ID an Admin."""
    await UserManager.change_role(RoleType.admin, user_id)


@router.put(
    "/users/{user_id}",
    dependencies=[Depends(oauth2_schema), Depends(is_admin)],
    status_code=200,
    response_model=UserResponse,
)
async def edit_user(user_id: int, user_data: UserEditRequest):
    """Update the specified User's data."""
    await UserManager.update_user(user_id, user_data)
    return await UserManager.get_user_by_id(user_id)


@router.delete(
    "/users/{user_id}/",
    dependencies=[Depends(oauth2_schema), Depends(is_admin)],
    status_code=204,
)
async def delete_user(user_id: int):
    """Delete the specified User by user_id."""
    await UserManager.delete_user(user_id)
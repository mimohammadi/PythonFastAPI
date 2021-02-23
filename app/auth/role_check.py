from typing import List

from fastapi import Depends, HTTPException
from jose import JWTError

from app.auth.auth_handler import oauth2_scheme, decode_jwt
from app.model import User, TokenData
from fastapi import status, HTTPException

from data.postgre_data import get_user, get_user_permission


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_jwt(token)
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    user = get_user(user_id=token_data.user_id)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    # if current_user.disabled:
    #    raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


class RoleChecker:
    def __init__(self, allowed_roles: List):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_active_user)):
        roles = get_user_permission(user.username)
        counter = 0
        for role in roles:
            if role not in self.allowed_roles:
                counter += 1
                # logger.debug(f"User with role {user.role} not in {self.allowed_roles}")
        if counter == len(roles):
            raise HTTPException(status_code=403, detail="Operation not permitted")




import psycopg2
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from data.connection.postgres.postgres_connection import get_connection
from .auth_handler import decode_jwt
# from ..model import TokenData


def verify_jwt(jwt_token: str) -> bool:
    is_token_valid: bool = False

    try:
        payload = decode_jwt(jwt_token)
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authorization code.")
    except(Exception, psycopg2.Error) as error:
        payload = None
        print(error)
    if payload:
        is_token_valid = True
    return user_id


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=401, detail="Invalid authentication scheme.")
            user_id = verify_jwt(credentials.credentials)
            if user_id is None:
                raise HTTPException(status_code=401, detail="Invalid token or expired token.")
            return user_id
        else:
            raise HTTPException(status_code=401, detail="Invalid authorization code.")

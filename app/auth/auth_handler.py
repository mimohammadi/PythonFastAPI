
import psycopg2
from jose import jwt
import time
from typing import Dict

from passlib.context import CryptContext

from fastapi.security import OAuth2PasswordBearer
import json

from data.redis_data import set_routes_to_cache, get_routes_from_cache

JWT_SECRET = "5af5e18073e3d3ffb4eefdb84f4e7705a58eacd8c09f3c2d0221904930cbe7fc"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 900
SALT = "authfirstsalt"


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    try:
        status = pwd_context.verify(SALT+plain_password, hashed_password)
    except (Exception, psycopg2.Error) as error:
        print(error)
    return status


def get_password_hash(password):
    return pwd_context.hash(SALT + password)


def token_response(token: str):
    return {
        "access_token": token, "token_type": "bearer"
    }


def decode_jwt(token: str) -> dict:
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded_token if decoded_token["expires"] >= time.time() else None
    except(Exception, psycopg2.Error) as error:
        return {}


def sign_jwt(user_id: str) -> Dict[str, str]:
    try:
        # data = {"sub": user_id}
        # data.update({"expires": time.time() + (ACCESS_TOKEN_EXPIRE_MINUTES * 60)})
        # token = jwt.encode(str(data), JWT_SECRET, algorithm=JWT_ALGORITHM)
        payload = {
            "user_id": user_id,
            "expires": time.time() + ACCESS_TOKEN_EXPIRE_SECONDS
            # str((ACCESS_TOKEN_EXPIRE_MINUTES * 60))
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        t = token_response(token)
        status = set_routes_to_cache('users_id:'+str(user_id), json.dumps(t),
                                     ACCESS_TOKEN_EXPIRE_SECONDS)
        if not status:
            return {"error": "Failed to set redis!"}
        print(get_routes_from_cache('users_id:'+str(user_id)))
        return t
    except (Exception, psycopg2.Error) as error:
        print(error)
        return {"error": error}



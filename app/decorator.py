# import simplejson as json
# from base64 import b64decode
import psycopg2
from fastapi import Header, HTTPException, Depends
from fastapi import status
from functools import wraps

from app.auth.role_check import RoleChecker, check_role

allow_create_resource = RoleChecker(["admin"])


def permissions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # t = kwargs['order']
            # d = dict((x, y) for x, y in t)
            v = check_role(["admin"], kwargs['user_id']) # d['user_id']
            if v is not None:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="user does not have access for this")

            return func(*args, **kwargs)
        except (Exception, psycopg2.Error) as error:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="user does not have access for this")

    # return wrapper

    return wrapper


def permissions1(required_permissions):
    def decorator_access(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # t = kwargs['order']
                # d = dict((x, y) for x, y in t)
                v = check_role(required_permissions, kwargs['user_id'])  # d['user_id']
                if v is not None:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                        detail="user does not have access for this")

                return func(*args, **kwargs)
            except (Exception, psycopg2.Error) as error:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="user does not have access for this")

        return wrapper

    return decorator_access
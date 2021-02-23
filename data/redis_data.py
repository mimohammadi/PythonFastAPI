from datetime import timedelta

from data.connection.redis.redis_connection import redis_connect

client = redis_connect()


def get_routes_from_cache(key: str) -> str:
    """Get data from redis."""

    val = client.get(key)
    return val


def set_routes_to_cache(key: str, value: str, expiration_second: int) -> bool:
    """Set data to redis."""

    return client.setex(key, timedelta(seconds=expiration_second), value=value, )

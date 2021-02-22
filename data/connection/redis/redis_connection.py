import sys

import redis


def redis_connect() -> redis.client.Redis:
    try:
        # redis_url = os.getenv('REDISTOGO_URL')
        #
        # urlparse.uses_netloc.append('redis')
        # url = urlparse.urlparse(redis_url)
        # client = Redis(host=url.hostname, port=url.port, db=0, password=url.password)
        client = redis.Redis(
            host='localhost',
            port=6379,
            # password="ubuntu",
            db=0
            # socket_timeout=5,
        )
        ping = client.ping()
        if ping is True:
            return client
    except redis.AuthenticationError:
        print("AuthenticationError")
        sys.exit(1)

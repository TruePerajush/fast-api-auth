import time
import uuid

from redis.asyncio import Redis

from my_fast_api.common.errors import AppError, Errors


class RateLimiter:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    async def check(
        self, prefix: str, identifier: str, limit: int, window: int
    ) -> None | AppError:
        key = f"rl:{prefix}:{identifier}"
        now_ms = int(time.time() * 1000)
        window_ms = window * 1000
        member = f"{now_ms}:{uuid.uuid7().hex}"

        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.zremrangebyscore(key, 0, now_ms - window_ms)
            pipe.zadd(key, {member: now_ms})
            pipe.zcard(key)
            pipe.pexpire(key, window_ms)
            _, _, count, _ = await pipe.execute()

        if count > limit:
            return Errors.too_many_requests(window)

        return None


rate_limiter = None

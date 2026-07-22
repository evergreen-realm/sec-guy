"""
Redis client for job persistence and checkpoints.
"""

import json
import logging
from typing import Optional, Dict, Any
import redis
from redis.exceptions import ConnectionError

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.host = host
        self.port = port
        self.db = db
        self._client = None
        self._connect()

    def _connect(self) -> None:
        try:
            self._client = redis.Redis(host=self.host, port=self.port, db=self.db, decode_responses=True)
            self._client.ping()
            logger.info("Connected to Redis")
        except ConnectionError:
            logger.warning("Redis not available; persistence disabled")
            self._client = None

    def set_job(self, job_id: str, data: Dict[str, Any], ttl: int = 604800) -> None:
        if self._client:
            self._client.setex(f"job:{job_id}", ttl, json.dumps(data, default=str))

    def get_job(self, job_id: str) -> Optional[Dict]:
        if self._client:
            val = self._client.get(f"job:{job_id}")
            if val:
                return json.loads(val)
        return None

    def delete_job(self, job_id: str) -> None:
        if self._client:
            self._client.delete(f"job:{job_id}")

    def list_job_ids(self) -> list:
        if self._client:
            keys = self._client.keys("job:*")
            return [k.split(":", 1)[1] for k in keys]
        return []

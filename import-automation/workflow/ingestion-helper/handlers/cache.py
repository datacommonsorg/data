import logging
import os
from flask import jsonify
import redis

def handle_clear_redis_cache(request_json):
    """Flushes the Redis cache."""
    logging.info("Action: clear_redis_cache")
    redis_host = os.environ.get("REDIS_HOST")
    redis_port = os.environ.get("REDIS_PORT", "6379")
    if redis_host:
        try:
            r = redis.Redis(host=redis_host, port=int(redis_port))
            r.flushall(asynchronous=True)
            logging.info(f"Redis cache at {redis_host}:{redis_port} flushed successfully (async).")
            return jsonify({'status': 'SUCCESS', 'message': 'Cache cleared'}), 200
        except Exception as e:
            logging.error(f"Failed to flush Redis cache: {e}")
            return jsonify({'status': 'ERROR', 'message': str(e)}), 500
    else:
        logging.warning("REDIS_HOST not set, skipping cache flush.")
        return jsonify({'status': 'SKIPPED', 'message': 'REDIS_HOST not set'}), 200
